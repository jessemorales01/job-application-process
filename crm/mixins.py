"""
ViewSet mixins for caching API responses.
"""
from rest_framework.response import Response
from django.core.cache import cache
from .cache_utils import get_cache_key, CACHE_PREFIXES, CACHE_TTL


class CacheResponseMixin:
    """
    Mixin to cache list and retrieve responses.
    
    Usage:
        class MyViewSet(CacheResponseMixin, viewsets.ModelViewSet):
            cache_prefix = 'my_model'
            cache_ttl = 300  # 5 minutes
    """
    cache_prefix = None
    cache_ttl = 300
    cache_user_specific = True
    
    def get_cache_key(self, action='list', **kwargs):
        """Generate cache key for the current request"""
        user_id = None
        if self.cache_user_specific and hasattr(self.request, 'user'):
            user_id = self.request.user.id if self.request.user.is_authenticated else None
        
        prefix = self.cache_prefix or self.get_queryset().model.__name__.lower()
        
        if action == 'retrieve':
            obj_id = kwargs.get('pk')
            return get_cache_key(f'{prefix}:detail', user_id=user_id, pk=obj_id)
        else:
            # Include query params in cache key for filtering
            query_params = dict(self.request.query_params)
            return get_cache_key(f'{prefix}:list', user_id=user_id, **query_params)
    
    def list(self, request, *args, **kwargs):
        """Cached list view"""
        cache_key = self.get_cache_key('list')
        cached_response = cache.get(cache_key)
        
        if cached_response is not None:
            return Response(cached_response)
        
        response = super().list(request, *args, **kwargs)
        cache.set(cache_key, response.data, self.cache_ttl)
        return response
    
    def retrieve(self, request, *args, **kwargs):
        """Cached retrieve view"""
        cache_key = self.get_cache_key('retrieve', pk=kwargs.get('pk'))
        cached_response = cache.get(cache_key)
        
        if cached_response is not None:
            return Response(cached_response)
        
        response = super().retrieve(request, *args, **kwargs)
        cache.set(cache_key, response.data, self.cache_ttl)
        return response
    
    def create(self, request, *args, **kwargs):
        """Clear cache on create"""
        response = super().create(request, *args, **kwargs)
        # Cache invalidation handled by signals, but clear list cache
        self._clear_list_cache()
        return response
    
    def update(self, request, *args, **kwargs):
        """Clear cache on update"""
        response = super().update(request, *args, **kwargs)
        self._clear_list_cache()
        self._clear_detail_cache(kwargs.get('pk'))
        return response
    
    def destroy(self, request, *args, **kwargs):
        """Clear cache on delete"""
        pk = kwargs.get('pk')
        response = super().destroy(request, *args, **kwargs)
        self._clear_list_cache()
        self._clear_detail_cache(pk)
        return response
    
    def _clear_list_cache(self):
        """Clear list cache for current user"""
        prefix = self.cache_prefix or self.get_queryset().model.__name__.lower()
        user_id = None
        if self.cache_user_specific and hasattr(self.request, 'user'):
            user_id = self.request.user.id if self.request.user.is_authenticated else None
        
        # Try pattern deletion (Redis)
        if hasattr(cache, 'delete_pattern'):
            cache_key_pattern = get_cache_key(f'{prefix}:list', user_id=user_id)
            try:
                cache.delete_pattern(f'{cache_key_pattern}*')
            except (AttributeError, NotImplementedError):
                # Fallback: delete common keys
                cache.delete(get_cache_key(f'{prefix}:list', user_id=user_id))
        else:
            # Fallback for non-Redis backends
            cache.delete(get_cache_key(f'{prefix}:list', user_id=user_id))
    
    def _clear_detail_cache(self, pk):
        """Clear detail cache for specific object"""
        if pk:
            cache_key = self.get_cache_key('retrieve', pk=pk)
            cache.delete(cache_key)

