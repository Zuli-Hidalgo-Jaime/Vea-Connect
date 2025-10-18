# Tests comentados temporalmente - la app vea_review no está en INSTALLED_APPS
# from django.test import TestCase
# from django.contrib.auth import get_user_model
# from django.urls import reverse
# from .models import Restaurant
# 
# class RestaurantReviewTest(TestCase):
#     def setUp(self):
#         self.user = get_user_model().objects.create_user(
#             username='testuser',
#             password='testpass123'
#         )
#         self.restaurant = Restaurant.objects.create(
#             name='Test Restaurant',
#             address='123 Test St',
#             phone='555-1234'
#         )
# 
#     def test_restaurant_creation(self):
#         self.assertEqual(self.restaurant.name, 'Test Restaurant')
#         self.assertEqual(self.restaurant.address, '123 Test St')
#         self.assertEqual(self.restaurant.phone, '555-1234')
