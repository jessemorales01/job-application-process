"""Cache utilities for optimizing database queries"""
from django.core.cache import cache
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from functools import wraps
import hashlib
import json


# Cache key prefixes
CACHE_PREFIXES = {
    'stages': 'stages',
    'applications': 'applications',
    'job_offers': 'job_offers',
    'assessments': 'assessments',
    'interactions': 'interactions',
    'email_accounts': 'email_accounts',
    'auto_detected_applications': 'auto_detected_applications',
    'user_apps': 'user_apps',
    'user_job_offers': 'user_job_offers',
    'user_assessments': 'user_assessments',
    'user_interactions': 'user_interactions',
}

# Cache TTLs (Time To Live) in seconds
CACHE_TTL = {
    'stages': 3600 * 24,  # 24 hours - stages rarely change
    'applications': 300,  # 5 minutes - applications change frequently
    'job_offers': 300,  # 5 minutes
    'assessments': 300,  # 5 minutes
    'interactions': 300,  # 5 minutes
    'email_accounts': 300,  # 5 minutes
    'auto_detected_applications': 300,  # 5 minutes
    'dashboard_stats': 60,  # 1 minute - stats change more frequently
}


def get_cache_key(prefix, user_id=None, **kwargs):
    """Generate a cache key with optional user ID and additional parameters"""
    key_parts = [prefix]
    
    if user_id:
        key_parts.append(f'user_{user_id}')
    
    if kwargs:
        # Sort kwargs for consistent key generation
        sorted_kwargs = sorted(kwargs.items())
        kwargs_str = json.dumps(sorted_kwargs, sort_keys=True)
        kwargs_hash = hashlib.md5(kwargs_str.encode()).hexdigest()[:8]
        key_parts.append(kwargs_hash)
    
    return ':'.join(key_parts)


def cache_result(ttl=None, key_func=None):
    """Decorator to cache function results"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                # Default: use function name + args hash
                key_parts = [func.__name__]
                if args or kwargs:
                    key_data = json.dumps((args, kwargs), sort_keys=True, default=str)
                    key_hash = hashlib.md5(key_data.encode()).hexdigest()[:8]
                    key_parts.append(key_hash)
                cache_key = ':'.join(key_parts)
            
            # Try to get from cache
            result = cache.get(cache_key)
            if result is not None:
                return result
            
            # Execute function and cache result
            result = func(*args, **kwargs)
            cache.set(cache_key, result, ttl or 300)
            return result
        
        # Add method to clear cache for this function
        wrapper.clear_cache = lambda: cache.delete_many([
            key for key in cache.keys(f'{func.__name__}:*')
        ]) if hasattr(cache, 'keys') else None
        
        return wrapper
    return decorator


def invalidate_user_cache(user_id, model_name):
    """Invalidate all cache entries for a specific user and model"""
    prefix = CACHE_PREFIXES.get(f'user_{model_name}', model_name)
    
    # Try to delete pattern matches (if using Redis/django-redis)
    try:
        if hasattr(cache, 'delete_pattern'):
            # Delete all keys matching: prefix:list:user_X:* and prefix:detail:user_X:*
            cache.delete_pattern(f'job_process_tracker:{prefix}:list:user_{user_id}:*')
            cache.delete_pattern(f'job_process_tracker:{prefix}:detail:user_{user_id}:*')
        elif hasattr(cache, '_cache') and hasattr(cache._cache, 'delete_pattern'):
            # django-redis specific
            cache._cache.delete_pattern(f'job_process_tracker:{prefix}:list:user_{user_id}:*')
            cache._cache.delete_pattern(f'job_process_tracker:{prefix}:detail:user_{user_id}:*')
        else:
            # For local memory cache, we can't do pattern deletion
            # Instead, we'll need to track keys or use a different strategy
            # For now, we'll delete common key patterns manually
            # This is a limitation of local memory cache
            pass  # Don't clear all cache - too aggressive
    except (AttributeError, NotImplementedError, TypeError):
        # Don't clear all cache as fallback - too aggressive for production
        pass


def invalidate_model_cache(model_name):
    """Invalidate all cache entries for a model (all users)"""
    prefix = CACHE_PREFIXES.get(model_name, model_name)
    
    try:
        if hasattr(cache, 'delete_pattern'):
            # Delete all keys matching: prefix:list:* and prefix:detail:*
            # Include KEY_PREFIX from settings
            cache.delete_pattern(f'job_process_tracker:{prefix}:list:*')
            cache.delete_pattern(f'job_process_tracker:{prefix}:detail:*')
        elif hasattr(cache, '_cache') and hasattr(cache._cache, 'delete_pattern'):
            # django-redis specific
            cache._cache.delete_pattern(f'job_process_tracker:{prefix}:list:*')
            cache._cache.delete_pattern(f'job_process_tracker:{prefix}:detail:*')
        else:
            # In production with Redis, pattern deletion will work
            pass
    except (AttributeError, NotImplementedError, TypeError):
        pass


# Signal handlers for automatic cache invalidation
@receiver(post_save, sender='crm.Stage')
@receiver(post_delete, sender='crm.Stage')
def invalidate_stage_cache(sender, **kwargs):
    """Invalidate stage cache when stages are created/updated/deleted"""
    invalidate_model_cache('stages')


@receiver(post_save, sender='crm.Application')
@receiver(post_delete, sender='crm.Application')
def invalidate_application_cache(sender, instance, **kwargs):
    """Invalidate application cache when applications are created/updated/deleted"""
    invalidate_model_cache('applications')
    if instance.created_by:
        invalidate_user_cache(instance.created_by.id, 'applications')


@receiver(post_save, sender='crm.JobOffer')
@receiver(post_delete, sender='crm.JobOffer')
def invalidate_joboffer_cache(sender, instance, **kwargs):
    """Invalidate job offer cache when job offers are created/updated/deleted"""
    invalidate_model_cache('job_offers')
    if instance.created_by:
        invalidate_user_cache(instance.created_by.id, 'job_offers')
    # Also invalidate related application cache
    if instance.application and instance.application.created_by:
        invalidate_user_cache(instance.application.created_by.id, 'applications')


@receiver(post_save, sender='crm.Assessment')
@receiver(post_delete, sender='crm.Assessment')
def invalidate_assessment_cache(sender, instance, **kwargs):
    """Invalidate assessment cache when assessments are created/updated/deleted"""
    invalidate_model_cache('assessments')
    if instance.created_by:
        invalidate_user_cache(instance.created_by.id, 'assessments')
    if instance.application and instance.application.created_by:
        invalidate_user_cache(instance.application.created_by.id, 'applications')


@receiver(post_save, sender='crm.Interaction')
@receiver(post_delete, sender='crm.Interaction')
def invalidate_interaction_cache(sender, instance, **kwargs):
    """Invalidate interaction cache when interactions are created/updated/deleted"""
    invalidate_model_cache('interactions')
    if instance.created_by:
        invalidate_user_cache(instance.created_by.id, 'interactions')
    if instance.application and instance.application.created_by:
        invalidate_user_cache(instance.application.created_by.id, 'applications')


@receiver(post_save, sender='crm.EmailAccount')
@receiver(post_delete, sender='crm.EmailAccount')
def invalidate_email_account_cache(sender, instance, **kwargs):
    """Invalidate email account cache when email accounts are created/updated/deleted"""
    invalidate_model_cache('email_accounts')
    if instance.user:
        invalidate_user_cache(instance.user.id, 'email_accounts')


@receiver(post_save, sender='crm.AutoDetectedApplication')
@receiver(post_delete, sender='crm.AutoDetectedApplication')
def invalidate_auto_detected_cache(sender, instance, **kwargs):
    """Invalidate auto-detected application cache when detected apps are created/updated/deleted"""
    invalidate_model_cache('auto_detected_applications')
    if instance.email_account and instance.email_account.user:
        invalidate_user_cache(instance.email_account.user.id, 'auto_detected_applications')
    # Also invalidate applications cache if merged
    if instance.merged_into_application and instance.merged_into_application.created_by:
        invalidate_user_cache(instance.merged_into_application.created_by.id, 'applications')

