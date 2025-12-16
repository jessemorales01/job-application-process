from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.test import APITestCase
from rest_framework import status
from .models import Stage, Application
from .serializers import ApplicationSerializer


class JobOfferModelTests(TestCase):
    """Test the JobOffer model"""
    
    def setUp(self):
        """Set up test user for created_by field"""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
    
    def test_can_create_job_offer(self):
        """Test that we can create a JobOffer with required fields"""
        from .models import JobOffer
        
        job_offer = JobOffer.objects.create(
            company_name="Tech Corp",
            position="Software Engineer",
            salary_range="100k-150k"
        )
        
        self.assertEqual(job_offer.company_name, "Tech Corp")
        self.assertEqual(job_offer.position, "Software Engineer")
        self.assertEqual(job_offer.salary_range, "100k-150k")
        self.assertIsNotNone(job_offer.id)
    
    def test_job_offer_with_created_by(self):
        """Test creating JobOffer with created_by user"""
        from .models import JobOffer
        
        job_offer = JobOffer.objects.create(
            company_name="Tech Corp",
            position="Software Engineer",
            salary_range="100k-150k",
            created_by=self.user
        )
        
        self.assertEqual(job_offer.created_by, self.user)
        self.assertEqual(job_offer.created_by.username, 'testuser')
    
    def test_job_offer_without_created_by(self):
        """Test that created_by can be None (SET_NULL behavior)"""
        from .models import JobOffer
        
        job_offer = JobOffer.objects.create(
            company_name="Tech Corp",
            position="Software Engineer",
            salary_range="100k-150k",
            created_by=None
        )
        
        self.assertIsNone(job_offer.created_by)
    
    def test_job_offer_str_method(self):
        """Test the __str__ method returns correct format"""
        from .models import JobOffer
        
        job_offer = JobOffer.objects.create(
            company_name="Tech Corp",
            position="Software Engineer",
            salary_range="100k-150k"
        )
        
        expected_str = "Software Engineer at Tech Corp"
        self.assertEqual(str(job_offer), expected_str)
    
    def test_job_offer_auto_timestamps(self):
        """Test that created_at and updated_at are auto-generated"""
        from .models import JobOffer
        from django.utils import timezone
        
        job_offer = JobOffer.objects.create(
            company_name="Tech Corp",
            position="Software Engineer",
            salary_range="100k-150k"
        )
        
        self.assertIsNotNone(job_offer.created_at)
        self.assertIsNotNone(job_offer.updated_at)
        self.assertLessEqual(job_offer.created_at, timezone.now())
        self.assertLessEqual(job_offer.updated_at, timezone.now())
    
    def test_job_offer_updated_at_changes_on_save(self):
        """Test that updated_at changes when object is saved"""
        from .models import JobOffer
        import time
        
        job_offer = JobOffer.objects.create(
            company_name="Tech Corp",
            position="Software Engineer",
            salary_range="100k-150k"
        )
        
        original_updated_at = job_offer.updated_at
        time.sleep(0.1)
        
        job_offer.position = "Senior Software Engineer"
        job_offer.save()
        
        self.assertGreater(job_offer.updated_at, original_updated_at)
    
    def test_job_offer_ordering(self):
        """Test that JobOffers are ordered by -created_at (newest first)"""
        from .models import JobOffer
        import time
        
        job1 = JobOffer.objects.create(
            company_name="Company A",
            position="Position A",
            salary_range="50k-70k"
        )
        time.sleep(0.1)
        
        job2 = JobOffer.objects.create(
            company_name="Company B",
            position="Position B",
            salary_range="80k-100k"
        )
        
        all_offers = list(JobOffer.objects.all())
        
        self.assertEqual(all_offers[0], job2)
        self.assertEqual(all_offers[1], job1)
    
    def test_job_offer_max_length_constraints(self):
        """Test that max_length constraints are enforced"""
        from .models import JobOffer
        from django.core.exceptions import ValidationError
        
        long_company_name = "A" * 201
        job_offer = JobOffer(
            company_name=long_company_name,
            position="Test Position",
            salary_range="50k-70k"
        )
        
        with self.assertRaises(Exception):
            job_offer.full_clean()
        
        long_position = "B" * 201
        job_offer = JobOffer(
            company_name="Test Company",
            position=long_position,
            salary_range="50k-70k"
        )
        
        with self.assertRaises(Exception):
            job_offer.full_clean()
        
        long_salary_range = "C" * 101
        job_offer = JobOffer(
            company_name="Test Company",
            position="Test Position",
            salary_range=long_salary_range
        )
        
        with self.assertRaises(Exception):
            job_offer.full_clean()
    
    def test_job_offer_user_relationship(self):
        """Test the reverse relationship from User to JobOffer"""
        from .models import JobOffer
        
        job1 = JobOffer.objects.create(
            company_name="Company A",
            position="Position A",
            salary_range="50k-70k",
            created_by=self.user
        )
        job2 = JobOffer.objects.create(
            company_name="Company B",
            position="Position B",
            salary_range="80k-100k",
            created_by=self.user
        )
        
        user_job_offers = self.user.job_offers.all()
        self.assertEqual(user_job_offers.count(), 2)
        self.assertIn(job1, user_job_offers)
        self.assertIn(job2, user_job_offers)
    
    def test_job_offer_user_set_null_on_delete(self):
        """Test that created_by is set to NULL when user is deleted"""
        from .models import JobOffer
        
        job_offer = JobOffer.objects.create(
            company_name="Tech Corp",
            position="Software Engineer",
            salary_range="100k-150k",
            created_by=self.user
        )
        
        job_offer_id = job_offer.id
        self.user.delete()
        
        job_offer.refresh_from_db()
        self.assertIsNone(job_offer.created_by)
        self.assertEqual(job_offer.id, job_offer_id)


class ApplicationCreationValidationTests(APITestCase):
    """Test application creation validation rules"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
    
    def test_cannot_create_application_without_stages(self):
        """Application creation should fail when no stages exist"""
        Stage.objects.all().delete()
        
        response = self.client.post('/api/applications/', {
            'company_name': 'Test Company',
        })
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('no stages exist', str(response.data).lower())
    
    def test_can_create_application_with_stages(self):
        """Application creation should succeed when stages exist"""
        Stage.objects.create(name="Applied", order=1)
        
        response = self.client.post('/api/applications/', {
            'company_name': 'Test Company',
        })
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['company_name'], 'Test Company')
    
    def test_application_auto_assigns_first_stage(self):
        """Application should auto-assign to first stage if none provided"""
        stage1 = Stage.objects.create(name="Applied", order=1)
        stage2 = Stage.objects.create(name="Interview", order=2)
        
        response = self.client.post('/api/applications/', {
            'company_name': 'Test Company',
        })
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['stage'], stage1.id)


class StageDeletionTests(APITestCase):
    """Test the stage deletion API endpoint"""
    
    def setUp(self):
        """Create test user, stage, and application"""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
        self.stage = Stage.objects.create(name="Applied", order=1)
    
    def test_delete_empty_stage_succeeds(self):
        """Deleting a stage with no applications should succeed"""
        response = self.client.delete(f'/api/stages/{self.stage.id}/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Stage.objects.filter(id=self.stage.id).exists())
    
    def test_delete_stage_with_applications_fails(self):
        """Deleting a stage with applications should return 400 error"""
        Application.objects.create(
            company_name="Test Company",
            stage=self.stage,
            created_by=self.user
        )
        
        response = self.client.delete(f'/api/stages/{self.stage.id}/')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue(Stage.objects.filter(id=self.stage.id).exists())
    
    def test_delete_stage_with_applications_returns_error_message(self):
        """Error message should include application count"""
        Application.objects.create(company_name="Company 1", stage=self.stage, created_by=self.user)
        Application.objects.create(company_name="Company 2", stage=self.stage, created_by=self.user)
        
        response = self.client.delete(f'/api/stages/{self.stage.id}/')
        self.assertIn('error', response.data)
        self.assertIn('2 application(s)', response.data['error'])
    
    def test_delete_stage_after_moving_applications_succeeds(self):
        """Stage can be deleted after applications are moved out"""
        other_stage = Stage.objects.create(name="Interview", order=2)
        application = Application.objects.create(
            company_name="Test Company",
            stage=self.stage,
            created_by=self.user
        )
        
        application.stage = other_stage
        application.save()
        
        response = self.client.delete(f'/api/stages/{self.stage.id}/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)


class ApplicationMovementTests(APITestCase):
    """Test moving applications between stages via API"""
    
    def setUp(self):
        """Create test user and stages"""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
        self.stage1 = Stage.objects.create(name="Applied", order=1)
        self.stage2 = Stage.objects.create(name="Interview", order=2)
    
    def test_move_application_to_different_stage(self):
        """Application can be moved from one stage to another via PATCH"""
        response = self.client.post('/api/applications/', {
            'company_name': 'Test Company',
            'stage': self.stage1.id
        })
        application_id = response.data['id']
        self.assertEqual(response.data['stage'], self.stage1.id)
        
        response = self.client.patch(f'/api/applications/{application_id}/', {
            'stage': self.stage2.id
        })
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['stage'], self.stage2.id)
        
        application = Application.objects.get(id=application_id)
        self.assertEqual(application.stage, self.stage2)
    
    def test_move_application_preserves_other_fields(self):
        """Moving an application should not change other fields"""
        response = self.client.post('/api/applications/', {
            'company_name': 'Test Company',
            'email': 'test@example.com',
            'salary_range': '100k-150k',
            'stage': self.stage1.id
        })
        application_id = response.data['id']
        original_company_name = response.data['company_name']
        original_email = response.data['email']
        
        response = self.client.patch(f'/api/applications/{application_id}/', {
            'stage': self.stage2.id
        })
        
        self.assertEqual(response.data['company_name'], original_company_name)
        self.assertEqual(response.data['email'], original_email)
        self.assertEqual(response.data['salary_range'], '100k-150k')


class JobOfferAPITests(APITestCase):
    """Test JobOffer API endpoints"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
    
    def test_can_create_job_offer(self):
        """Test creating a job offer via API"""
        response = self.client.post('/api/job-offers/', {
            'company_name': 'Tech Corp',
            'position': 'Software Engineer',
            'salary_range': '100k-150k'
        })
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['company_name'], 'Tech Corp')
        self.assertEqual(response.data['position'], 'Software Engineer')
        self.assertEqual(response.data['salary_range'], '100k-150k')
    
    def test_can_list_job_offers(self):
        """Test listing job offers via API"""
        from .models import JobOffer
        
        JobOffer.objects.create(
            company_name='Company A',
            position='Position A',
            salary_range='80k-100k',
            created_by=self.user
        )
        JobOffer.objects.create(
            company_name='Company B',
            position='Position B',
            salary_range='120k-150k',
            created_by=self.user
        )
        
        response = self.client.get('/api/job-offers/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
    
    def test_can_update_job_offer(self):
        """Test updating a job offer via API"""
        from .models import JobOffer
        
        job_offer = JobOffer.objects.create(
            company_name='Tech Corp',
            position='Software Engineer',
            salary_range='100k-150k',
            created_by=self.user
        )
        
        response = self.client.patch(f'/api/job-offers/{job_offer.id}/', {
            'salary_range': '120k-160k'
        })
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['salary_range'], '120k-160k')
        self.assertEqual(response.data['company_name'], 'Tech Corp')
    
    def test_can_delete_job_offer(self):
        """Test deleting a job offer via API"""
        from .models import JobOffer
        
        job_offer = JobOffer.objects.create(
            company_name='Tech Corp',
            position='Software Engineer',
            salary_range='100k-150k',
            created_by=self.user
        )
        
        response = self.client.delete(f'/api/job-offers/{job_offer.id}/')
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(JobOffer.objects.filter(id=job_offer.id).exists())
    
    def test_user_only_sees_own_job_offers(self):
        """Test that users only see job offers they created"""
        from .models import JobOffer
        
        other_user = User.objects.create_user(
            username='otheruser',
            password='testpass123'
        )
        
        JobOffer.objects.create(
            company_name='My Company',
            position='My Position',
            salary_range='100k',
            created_by=self.user
        )
        JobOffer.objects.create(
            company_name='Other Company',
            position='Other Position',
            salary_range='200k',
            created_by=other_user
        )
        
        response = self.client.get('/api/job-offers/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['company_name'], 'My Company')
