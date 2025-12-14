from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.test import APITestCase
from rest_framework import status
from .models import Stage, Lead
from .serializers import LeadSerializer, STAGE_THRESHOLD_LOW, STAGE_THRESHOLD_MEDIUM
from .ml_service import predict_win_score


class StageAutoAssignTests(TestCase):
    """Test the auto-assign logic in LeadSerializer.get_stage_by_value()"""
    
    def setUp(self):
        """Create test stages before each test"""
        self.stage1 = Stage.objects.create(name="Small Deals", order=1)
        self.stage2 = Stage.objects.create(name="Medium Deals", order=2)
        self.stage3 = Stage.objects.create(name="Large Deals", order=3)
        self.serializer = LeadSerializer()
    
    def test_low_value_assigns_first_stage(self):
        """Values below STAGE_THRESHOLD_LOW should go to first stage"""
        stage = self.serializer.get_stage_by_value(500)
        self.assertEqual(stage, self.stage1)
    
    def test_medium_value_assigns_second_stage(self):
        """Values between thresholds should go to second stage"""
        stage = self.serializer.get_stage_by_value(5000)
        self.assertEqual(stage, self.stage2)
    
    def test_high_value_assigns_third_stage(self):
        """Values at or above STAGE_THRESHOLD_MEDIUM should go to third stage"""
        stage = self.serializer.get_stage_by_value(50000)
        self.assertEqual(stage, self.stage3)
    
    def test_boundary_low_threshold(self):
        """Test exact boundary at STAGE_THRESHOLD_LOW (1000)"""
        stage = self.serializer.get_stage_by_value(999)
        self.assertEqual(stage, self.stage1)
        stage = self.serializer.get_stage_by_value(STAGE_THRESHOLD_LOW)
        self.assertEqual(stage, self.stage2)
    
    def test_boundary_medium_threshold(self):
        """Test exact boundary at STAGE_THRESHOLD_MEDIUM (10000)"""
        stage = self.serializer.get_stage_by_value(9999)
        self.assertEqual(stage, self.stage2)
        stage = self.serializer.get_stage_by_value(STAGE_THRESHOLD_MEDIUM)
        self.assertEqual(stage, self.stage3)
    
    def test_no_stages_returns_none(self):
        """When no stages exist it should return None (leads go to backlog)"""
        Stage.objects.all().delete()
        stage = self.serializer.get_stage_by_value(5000)
        self.assertIsNone(stage)
    
    def test_only_one_stage_exists(self):
        """With only one stage all values should go to that stage"""
        Stage.objects.filter(order__gt=1).delete()
        self.assertEqual(self.serializer.get_stage_by_value(100), self.stage1)
        self.assertEqual(self.serializer.get_stage_by_value(5000), self.stage1)
        self.assertEqual(self.serializer.get_stage_by_value(50000), self.stage1)
    
    def test_only_two_stages_exist(self):
        """With two stages high values should go to last stage"""
        Stage.objects.filter(order=3).delete()
        self.assertEqual(self.serializer.get_stage_by_value(100), self.stage1)
        self.assertEqual(self.serializer.get_stage_by_value(5000), self.stage2)
        self.assertEqual(self.serializer.get_stage_by_value(50000), self.stage2)
    
    def test_zero_value(self):
        """Zero value should go to first stage"""
        stage = self.serializer.get_stage_by_value(0)
        self.assertEqual(stage, self.stage1)


class LeadCreationValidationTests(APITestCase):
    """Test lead creation validation rules"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
    
    def test_cannot_create_lead_without_stages(self):
        """Lead creation should fail when no stages exist"""
        Stage.objects.all().delete()
        
        response = self.client.post('/api/leads/', {
            'name': 'Test Lead',
            'email': 'test@example.com'
        })
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('no stages exist', str(response.data).lower())
    
    def test_can_create_lead_with_stages(self):
        """Lead creation should succeed when stages exist"""
        Stage.objects.create(name="Test Stage", order=1)
        
        response = self.client.post('/api/leads/', {
            'name': 'Test Lead',
            'email': 'test@example.com'
        })
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)


class MLPredictionTests(TestCase):
    """Test the ML prediction service predict_win_score()"""
    
    def setUp(self):
        """Create test lead"""
        self.lead = Lead.objects.create(
            name="Test Lead",
            email="test@example.com",
            estimated_value=5000,
            status="qualified",
            phone="555-1234",
            company="Test Company"
        )
    
    def test_prediction_returns_float(self):
        """Prediction should return a float between 0 and 1"""
        score = predict_win_score(self.lead)
        self.assertIsNotNone(score)
        self.assertIsInstance(score, float)
        self.assertGreaterEqual(score, 0)
        self.assertLessEqual(score, 1)
    
    def test_qualified_status_higher_than_new(self):
        """Qualified leads should have higher win score than new leads"""
        self.lead.status = "qualified"
        self.lead.save()
        qualified_score = predict_win_score(self.lead)
        
        self.lead.status = "new"
        self.lead.save()
        new_score = predict_win_score(self.lead)
        
        self.assertGreater(qualified_score, new_score)
    
    def test_lost_status_low_score(self):
        """Lost leads should have low win score"""
        self.lead.status = "lost"
        self.lead.save()
        score = predict_win_score(self.lead)
        self.assertLess(score, 0.5)
    
    def test_high_value_increases_score(self):
        """Higher estimated value should increase win score"""
        self.lead.estimated_value = 100
        self.lead.save()
        low_value_score = predict_win_score(self.lead)
        
        self.lead.estimated_value = 50000
        self.lead.save()
        high_value_score = predict_win_score(self.lead)
        
        self.assertGreater(high_value_score, low_value_score)
    
    def test_contact_info_increases_score(self):
        """Leads with phone and company should score higher"""
        self.lead.phone = "555-1234"
        self.lead.company = "Test Company"
        self.lead.save()
        with_info_score = predict_win_score(self.lead)
        
        self.lead.phone = ""
        self.lead.company = ""
        self.lead.save()
        without_info_score = predict_win_score(self.lead)
        
        self.assertGreater(with_info_score, without_info_score)
    
    def test_none_estimated_value_handled(self):
        """Lead with None estimated_value should not crash"""
        self.lead.estimated_value = None
        self.lead.save()
        score = predict_win_score(self.lead)
        self.assertIsNotNone(score)


class StageDeletionTests(APITestCase):
    """Test the stage deletion API endpoint"""
    
    def setUp(self):
        """Create test user, stage, and lead"""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
        self.stage = Stage.objects.create(name="Test Stage", order=1)
    
    def test_delete_empty_stage_succeeds(self):
        """Deleting a stage with no leads should succeed"""
        response = self.client.delete(f'/api/stages/{self.stage.id}/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Stage.objects.filter(id=self.stage.id).exists())
    
    def test_delete_stage_with_leads_fails(self):
        """Deleting a stage with leads should return 400 error"""
        Lead.objects.create(
            name="Test Lead",
            email="test@example.com",
            stage=self.stage,
            created_by=self.user
        )
        
        response = self.client.delete(f'/api/stages/{self.stage.id}/')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue(Stage.objects.filter(id=self.stage.id).exists())
    
    def test_delete_stage_with_leads_returns_error_message(self):
        """Error message should include lead count"""
        Lead.objects.create(name="Lead 1", email="lead1@example.com", stage=self.stage, created_by=self.user)
        Lead.objects.create(name="Lead 2", email="lead2@example.com", stage=self.stage, created_by=self.user)
        
        response = self.client.delete(f'/api/stages/{self.stage.id}/')
        self.assertIn('error', response.data)
        self.assertIn('2 lead(s)', response.data['error'])
    
    def test_delete_stage_after_moving_leads_succeeds(self):
        """Stage can be deleted after leads are moved out"""
        other_stage = Stage.objects.create(name="Other Stage", order=2)
        lead = Lead.objects.create(
            name="Test Lead",
            email="test@example.com",
            stage=self.stage,
            created_by=self.user
        )
        
        # Move lead to other stage
        lead.stage = other_stage
        lead.save()
        
        # Now deletion should succeed
        response = self.client.delete(f'/api/stages/{self.stage.id}/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)


class LeadMovementTests(APITestCase):
    """Test moving leads between stages via API"""
    
    def setUp(self):
        """Create test user and stages"""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
        self.stage1 = Stage.objects.create(name="Stage 1", order=1)
        self.stage2 = Stage.objects.create(name="Stage 2", order=2)
    
    def test_move_lead_to_different_stage(self):
        """Lead can be moved from one stage to another via PATCH"""
        response = self.client.post('/api/leads/', {
            'name': 'Test Lead',
            'email': 'test@example.com',
            'stage': self.stage1.id
        })
        lead_id = response.data['id']
        self.assertEqual(response.data['stage'], self.stage1.id)
        
        response = self.client.patch(f'/api/leads/{lead_id}/', {
            'stage': self.stage2.id
        })
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['stage'], self.stage2.id)
        
        lead = Lead.objects.get(id=lead_id)
        self.assertEqual(lead.stage, self.stage2)
    
    def test_move_lead_preserves_other_fields(self):
        """Moving a lead should not change other fields"""
        response = self.client.post('/api/leads/', {
            'name': 'Test Lead',
            'email': 'test@example.com',
            'estimated_value': 5000,
            'status': 'qualified',
            'stage': self.stage1.id
        })
        lead_id = response.data['id']
        original_win_score = response.data['win_score']
        
        response = self.client.patch(f'/api/leads/{lead_id}/', {
            'stage': self.stage2.id
        })
        
        # Other fields should be unchanged
        self.assertEqual(response.data['name'], 'Test Lead')
        self.assertEqual(response.data['estimated_value'], '5000.00')
        self.assertEqual(response.data['status'], 'qualified')
        self.assertEqual(response.data['win_score'], original_win_score)


class WinScoreCacheTests(APITestCase):
    """Test that win_score is cached and only recalculated when needed"""
    
    def setUp(self):
        """Create test user and stage"""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
        self.stage = Stage.objects.create(name="Test Stage", order=1)
    
    def test_win_score_populated_on_create(self):
        """win_score should be calculated when lead is created via API"""
        response = self.client.post('/api/leads/', {
            'name': 'New Lead',
            'email': 'new@example.com',
            'estimated_value': 5000,
            'status': 'qualified'
        })
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIsNotNone(response.data['win_score'])
        self.assertGreaterEqual(response.data['win_score'], 0)
        self.assertLessEqual(response.data['win_score'], 1)
    
    def test_win_score_recalculated_on_status_change(self):
        """win_score should update when status changes"""
        # Create lead with qualified status
        response = self.client.post('/api/leads/', {
            'name': 'Test Lead',
            'email': 'test@example.com',
            'estimated_value': 5000,
            'status': 'qualified',
            'phone': '555-1234',
            'company': 'Test Co'
        })
        lead_id = response.data['id']
        qualified_score = response.data['win_score']
        
        # Change status to lost
        response = self.client.patch(f'/api/leads/{lead_id}/', {
            'status': 'lost'
        })
        lost_score = response.data['win_score']
        
        # Lost should have lower score than qualified
        self.assertLess(lost_score, qualified_score)
    
    def test_win_score_recalculated_on_value_change(self):
        """win_score should update when estimated_value changes"""
        response = self.client.post('/api/leads/', {
            'name': 'Test Lead',
            'email': 'test@example.com',
            'estimated_value': 100,
            'status': 'qualified'
        })
        lead_id = response.data['id']
        low_value_score = response.data['win_score']
        
        # Increase value significantly
        response = self.client.patch(f'/api/leads/{lead_id}/', {
            'estimated_value': 50000
        })
        high_value_score = response.data['win_score']
        
        self.assertGreater(high_value_score, low_value_score)
    
    def test_win_score_not_recalculated_on_name_change(self):
        """win_score should NOT change when irrelevant fields change"""
        response = self.client.post('/api/leads/', {
            'name': 'Original Name',
            'email': 'test@example.com',
            'estimated_value': 5000,
            'status': 'qualified'
        })
        lead_id = response.data['id']
        original_score = response.data['win_score']
        
        # Change name (should not affect win_score)
        response = self.client.patch(f'/api/leads/{lead_id}/', {
            'name': 'Updated Name'
        })
        
        self.assertEqual(response.data['win_score'], original_score)
    
    def test_win_score_persisted_in_database(self):
        """win_score should be stored in database, not recalculated on read"""
        response = self.client.post('/api/leads/', {
            'name': 'Test Lead',
            'email': 'test@example.com',
            'estimated_value': 5000,
            'status': 'qualified'
        })
        lead_id = response.data['id']
        
        # Fetch from database directly
        lead = Lead.objects.get(id=lead_id)
        self.assertIsNotNone(lead.win_score)
        self.assertEqual(lead.win_score, response.data['win_score'])
