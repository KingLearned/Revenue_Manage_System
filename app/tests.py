from django.test import TestCase

# Create your tests here.
from django.test import TestCase
from django.utils import timezone
from datetime import date
from freezegun import freeze_time
from .models import User, LGA, Ward
from unittest.mock import patch
from app.tasks import send_otp_to_user

class UserModelTestCase(TestCase):

    def setUp(self):
        pass

    @patch('app.tasks.send_otp_to_user.apply_async')
    def test_send_otp(self, mock_apply_async):
        user = User.objects.create(username='admin', phone_number='08145497813')
        user.send_otp()
        
        mock_apply_async.assert_called_once_with((user.id, 'sms'), queue='account-verification')

    # def test_user_creation(self):
    #     lga = LGA.objects.create(name='Test LGA')
    #     ward = Ward.objects.create(name='Test Ward', lga=lga)

    #     user = User.objects.create(
    #         username='Jim123',
    #         first_name='Jack',
    #         last_name='Jim',
    #         abssin_num=123,
    #         title='Mr',
    #         is_agent=True,
    #         is_enforcer=False,
    #         marital_status='married',
    #         gender='male',
    #         phone_number='1234567890',
    #         dob=date(1990, 1, 1),
    #         occupation='Engineer',
    #         address='Test Address',
    #         state_of_origin='Test State',
    #         lga=lga,
    #         ward=ward,
    #         place_of_birth='Test City',
    #         next_of_kin='Test Next of Kin',
    #         passport='path/to/passport.jpg',  # Replace with the actual path
    #         bvn_number='12345678901',
    #         nin_number='98765432101',
    #         bussiness_name='Test Business',
    #         account_number='1234567890',
    #         balance=1000.00,
    #         amount_owed=500.00,
    #         owing=True,
    #         account_type='INDIVIDUAL',
    #         # Add other necessary fields
    #     )

    #     self.assertEqual(User.objects.count(), 1)
    #     self.assertEqual(user.abssin_num, 123)
    #     self.assertEqual(user.title, 'Mr')
    #     self.assertTrue(user.is_agent)
    #     self.assertFalse(user.is_enforcer)
    #     self.assertEqual(user.marital_status, 'married')
    #     self.assertEqual(user.gender, 'male')
    #     self.assertEqual(user.phone_number, '1234567890')
    #     self.assertEqual(user.dob, date(1990, 1, 1))
    #     self.assertEqual(user.occupation, 'Engineer')
    #     self.assertEqual(user.address, 'Test Address')
    #     self.assertEqual(user.state_of_origin, 'Test State')
    #     self.assertEqual(user.lga, lga)
    #     self.assertEqual(user.ward, ward)
    #     self.assertEqual(user.place_of_birth, 'Test City')
    #     self.assertEqual(user.next_of_kin, 'Test Next of Kin')
    #     self.assertEqual(user.passport, 'path/to/passport.jpg')
    #     self.assertEqual(user.bvn_number, '12345678901')
    #     self.assertEqual(user.nin_number, '98765432101')
    #     self.assertEqual(user.bussiness_name, 'Test Business')
    #     self.assertEqual(user.account_number, '1234567890')
    #     self.assertEqual(user.balance, 1000.00)
    #     self.assertEqual(user.amount_owed, 500.00)
    #     self.assertTrue(user.owing)
    #     self.assertEqual(user.account_type, 'INDIVIDUAL')

    # def test_user_properties(self):
    #     lga = LGA.objects.create(name='Test LGA')
    #     ward = Ward.objects.create(name='Test Ward', lga=lga)

    #     user = User.objects.create(
    #         username='Jim123',
    #         first_name='Jack',
    #         last_name='Jim',
    #         abssin_num=123,
    #         title='Mr',
    #         is_agent=True,
    #         is_enforcer=False,
    #         marital_status='married',
    #         gender='male',
    #         phone_number='1234567890',
    #         dob=date(1990, 1, 1),
    #         occupation='Engineer',
    #         address='Test Address',
    #         state_of_origin='Test State',
    #         lga=lga,
    #         ward=ward,
    #         place_of_birth='Test City',
    #         next_of_kin='Test Next of Kin',
    #         passport='path/to/passport.jpg',  # Replace with the actual path
    #         bvn_number='12345678901',
    #         nin_number='98765432101',
    #         bussiness_name='Test Business',
    #         account_number='1234567890',
    #         balance=1000.00,
    #         amount_owed=500.00,
    #         owing=True,
    #         account_type='INDIVIDUAL',
    #         # Add other necessary fields
    #     )

    #     self.assertFalse(user.is_admin)
    #     self.assertFalse(user.is_super_admin)

    #     self.assertTrue(user.is_super_admin)

    #     self.assertEqual(user.full_name, 'Jack Jim')

    #     self.assertFalse(user.is_admin_type)

    #     with freeze_time("2023-01-01"):
    #         user.dob = date(1990, 1, 1)
    #         user.save()
    #         self.assertEqual(user.age, 33)

    def tearDown(self):
        pass
