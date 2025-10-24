"""
Tests unitarios para WhatsApp Handlers
"""
from django.test import TestCase
from unittest.mock import Mock, patch, MagicMock
from apps.whatsapp_bot.handlers import WhatsAppBotHandler
from apps.whatsapp_bot.models import WhatsAppInteraction, WhatsAppContext


class TestWhatsAppBotHandler(TestCase):
    """Tests para WhatsAppBotHandler"""
    
    def setUp(self):
        self.handler = WhatsAppBotHandler()
    
    def test_handler_initialization(self):
        """Test inicialización del handler"""
        self.assertIsNotNone(self.handler)
        self.assertIsNotNone(self.handler.acs_service)
        self.assertIsNotNone(self.handler.template_service)
        self.assertIsNotNone(self.handler.logging_service)
    
    @patch('apps.whatsapp_bot.handlers.ACSService')
    @patch('apps.whatsapp_bot.handlers.TemplateService')
    @patch('apps.whatsapp_bot.handlers.LoggingService')
    def test_handler_with_custom_services(self, mock_logging, mock_template, mock_acs):
        """Test handler con servicios personalizados"""
        handler = WhatsAppBotHandler(
            acs_service=mock_acs,
            template_service=mock_template,
            logging_service=mock_logging
        )
        self.assertEqual(handler.acs_service, mock_acs)
        self.assertEqual(handler.template_service, mock_template)
        self.assertEqual(handler.logging_service, mock_logging)
    
    def test_detect_intent_donations(self):
        """Test detección de intent para donaciones"""
        message = "Quiero hacer una donación"
        intent = self.handler.detect_intent(message)
        self.assertEqual(intent, 'donations')
    
    def test_detect_intent_contact(self):
        """Test detección de intent para contacto"""
        message = "Necesito contactar al ministerio"
        intent = self.handler.detect_intent(message)
        self.assertEqual(intent, 'contact')
    
    def test_detect_intent_events(self):
        """Test detección de intent para eventos"""
        message = "¿Cuándo es el próximo evento?"
        intent = self.handler.detect_intent(message)
        self.assertEqual(intent, 'events')
    
    def test_detect_intent_general(self):
        """Test detección de intent general"""
        message = "Hola, ¿cómo estás?"
        intent = self.handler.detect_intent(message)
        self.assertEqual(intent, 'general')
    
    def test_get_template_for_intent_donations(self):
        """Test obtención de template para donaciones"""
        template = self.handler.get_template_for_intent('donations')
        self.assertEqual(template, 'vea_info_donativos')
    
    def test_get_template_for_intent_contact(self):
        """Test obtención de template para contacto"""
        template = self.handler.get_template_for_intent('contact')
        self.assertEqual(template, 'vea_contacto_ministerio')
    
    def test_get_template_for_intent_events(self):
        """Test obtención de template para eventos"""
        template = self.handler.get_template_for_intent('events')
        self.assertEqual(template, 'vea_event_info')
    
    def test_get_template_for_intent_general(self):
        """Test obtención de template para general"""
        template = self.handler.get_template_for_intent('general')
        self.assertEqual(template, 'vea_request_received')
    
    def test_get_template_for_intent_unknown(self):
        """Test obtención de template para intent desconocido"""
        template = self.handler.get_template_for_intent('unknown')
        self.assertEqual(template, 'vea_request_received')
    
    @patch('apps.whatsapp_bot.handlers.OpenAIService')
    def test_generate_fallback_response(self, mock_openai_class):
        """Test generación de respuesta de fallback"""
        # Mock OpenAI service
        mock_openai = Mock()
        mock_openai.generate_chat_response.return_value = "Respuesta de fallback generada"
        mock_openai_class.return_value = mock_openai
        
        message = "Mensaje de prueba"
        context = "Contexto de conversación"
        
        response = self.handler.generate_fallback_response(message, context)
        
        self.assertEqual(response, "Respuesta de fallback generada")
        mock_openai.generate_chat_response.assert_called_once()
    
    def test_process_message_success(self):
        """Test procesamiento exitoso de mensaje"""
        # Crear datos de prueba
        message_data = {
            'from': '+1234567890',
            'message': 'Quiero hacer una donación',
            'timestamp': '2024-01-01T12:00:00Z'
        }
        
        # Mock servicios
        with patch.object(self.handler.acs_service, 'send_text_message') as mock_send:
            mock_send.return_value = {'success': True, 'message_id': 'msg-123'}
            
            result = self.handler.process_message(message_data)
            
            self.assertTrue(result['success'])
            self.assertIn('response', result)
            mock_send.assert_called_once()
    
    def test_process_message_failure(self):
        """Test procesamiento fallido de mensaje"""
        # Crear datos de prueba con error
        message_data = {
            'from': '+1234567890',
            'message': 'Mensaje de prueba',
            'timestamp': '2024-01-01T12:00:00Z'
        }
        
        # Mock servicios para que fallen
        with patch.object(self.handler.acs_service, 'send_text_message') as mock_send:
            mock_send.side_effect = Exception("Error de envío")
            
            result = self.handler.process_message(message_data)
            
            self.assertFalse(result['success'])
            self.assertIn('error', result)
    
    def test_handle_donation_intent(self):
        """Test manejo de intent de donación"""
        # Mock template service
        with patch.object(self.handler.template_service, 'prepare_template_parameters') as mock_prepare:
            mock_prepare.return_value = {
                'customer_name': 'Juan',
                'ministry_name': 'Música',
                'bank_name': 'Banco Test',
                'beneficiary_name': 'Juan Pérez',
                'account_number': '1234567890',
                'clabe_number': '012345678901234567',
                'contact_name': 'María',
                'contact_phone': '+1234567890'
            }
            
            # Mock ACS service
            with patch.object(self.handler.acs_service, 'send_text_message') as mock_send:
                mock_send.return_value = {'success': True, 'message_id': 'msg-123'}
                
                result = self.handler.handle_donation_intent('+1234567890', 'Juan')
                
                self.assertTrue(result['success'])
                mock_prepare.assert_called_once()
                mock_send.assert_called_once()
    
    def test_handle_contact_intent(self):
        """Test manejo de intent de contacto"""
        # Mock template service
        with patch.object(self.handler.template_service, 'prepare_template_parameters') as mock_prepare:
            mock_prepare.return_value = {
                'customer_name': 'Juan',
                'ministry_name': 'Música',
                'contact_name': 'María',
                'contact_phone': '+1234567890'
            }
            
            # Mock ACS service
            with patch.object(self.handler.acs_service, 'send_text_message') as mock_send:
                mock_send.return_value = {'success': True, 'message_id': 'msg-123'}
                
                result = self.handler.handle_contact_intent('+1234567890', 'Juan', 'Música')
                
                self.assertTrue(result['success'])
                mock_prepare.assert_called_once()
                mock_send.assert_called_once()
    
    def test_handle_event_intent(self):
        """Test manejo de intent de evento"""
        # Mock template service
        with patch.object(self.handler.template_service, 'prepare_template_parameters') as mock_prepare:
            mock_prepare.return_value = {
                'customer_name': 'Juan',
                'event_name': 'Concierto de Navidad',
                'event_date': '2024-12-25',
                'event_location': 'Iglesia Principal'
            }
            
            # Mock ACS service
            with patch.object(self.handler.acs_service, 'send_text_message') as mock_send:
                mock_send.return_value = {'success': True, 'message_id': 'msg-123'}
                
                result = self.handler.handle_event_intent('+1234567890', 'Juan', 'Concierto de Navidad')
                
                self.assertTrue(result['success'])
                mock_prepare.assert_called_once()
                mock_send.assert_called_once()
    
    def test_handle_general_intent(self):
        """Test manejo de intent general"""
        # Mock template service
        with patch.object(self.handler.template_service, 'prepare_template_parameters') as mock_prepare:
            mock_prepare.return_value = {
                'customer_name': 'Juan',
                'request_summary': 'Solicitud general'
            }
            
            # Mock ACS service
            with patch.object(self.handler.acs_service, 'send_text_message') as mock_send:
                mock_send.return_value = {'success': True, 'message_id': 'msg-123'}
                
                result = self.handler.handle_general_intent('+1234567890', 'Juan', 'Solicitud general')
                
                self.assertTrue(result['success'])
                mock_prepare.assert_called_once()
                mock_send.assert_called_once()
    
    def test_log_interaction(self):
        """Test logging de interacción"""
        # Mock logging service
        with patch.object(self.handler.logging_service, 'log_interaction') as mock_log:
            mock_log.return_value = {'success': True}
            
            self.handler.log_interaction(
                phone_number='+1234567890',
                message_content='Test message',
                intent='donations',
                template_used='vea_info_donativos',
                response_content='Test response'
            )
            
            mock_log.assert_called_once()
    
    def test_get_context(self):
        """Test obtención de contexto"""
        # Mock logging service
        with patch.object(self.handler.logging_service, 'get_context') as mock_get:
            mock_get.return_value = WhatsAppContext(
                phone_number='+1234567890',
                context_data={'last_intent': 'donations', 'step': 1}
            )
            
            context = self.handler.get_context('+1234567890')
            
            self.assertIsNotNone(context)
            mock_get.assert_called_once_with('+1234567890')
    
    def test_update_context(self):
        """Test actualización de contexto"""
        # Mock logging service
        with patch.object(self.handler.logging_service, 'log_context') as mock_log:
            mock_log.return_value = {'success': True}
            
            self.handler.update_context(
                phone_number='+1234567890',
                context_data={'last_intent': 'donations', 'step': 2}
            )
            
            mock_log.assert_called_once()
    
    def test_error_handling(self):
        """Test manejo de errores"""
        # Test con datos inválidos
        result = self.handler.process_message({})
        
        self.assertFalse(result['success'])
        self.assertIn('error', result)
    
    def test_validation(self):
        """Test validación de datos"""
        # Test con número de teléfono inválido
        result = self.handler.process_message({
            'from': 'invalid-phone',
            'message': 'Test message',
            'timestamp': '2024-01-01T12:00:00Z'
        })
        
        self.assertFalse(result['success'])
        self.assertIn('error', result) 

    def test_try_template_response_no_template(self):
        handler = self.handler
        handler.template_service.get_template_for_intent = Mock(return_value=None)
        result = handler._try_template_response('+123', 'msg', 'donations', {}, {})
        self.assertFalse(result['success'])
        self.assertIn('No template', result['error'])

    def test_try_template_response_missing_params(self):
        mock_template = Mock()
        mock_template.parameters = ['param1', 'param2']
        handler = self.handler
        handler.template_service.get_template_for_intent = Mock(return_value=mock_template)
        handler.template_service.prepare_template_parameters = Mock(return_value={'param1': 'valor'})
        result = handler._try_template_response('+123', 'msg', 'donations', {}, {})
        self.assertFalse(result['success'])
        self.assertIn('Missing parameters', result['error'])

    def test_try_template_response_exception(self):
        mock_template = Mock()
        mock_template.parameters = []
        handler = self.handler
        handler.template_service.get_template_for_intent = Mock(return_value=mock_template)
        handler.template_service.prepare_template_parameters = Mock(side_effect=Exception('error test'))
        result = handler._try_template_response('+123', 'msg', 'donations', {}, {})
        self.assertFalse(result['success'])
        self.assertIn('error test', result['error'])

    def test_try_template_response_acs_failure(self):
        mock_template = Mock()
        mock_template.parameters = []
        handler = self.handler
        handler.template_service.get_template_for_intent = Mock(return_value=mock_template)
        handler.template_service.prepare_template_parameters = Mock(return_value={})
        handler.template_service.send_template_response = Mock(return_value={'success': False, 'error': 'fail'})
        result = handler._try_template_response('+123', 'msg', 'donations', {}, {})
        self.assertFalse(result['success'])
        self.assertIn('ACS response failed', result['error'])

    def test_try_openai_fallback_exception(self):
        handler = self.handler
        handler._create_fallback_prompt = Mock(return_value='prompt')
        handler.embedding_manager.generate_embedding = Mock(side_effect=Exception('embedding error'))
        handler.acs_service.send_text_message = Mock(return_value={'success': True, 'message_id': 'id'})
        result = handler._try_openai_fallback('+123', 'msg', 'general', {})
        self.assertTrue(result['success'])
        self.assertIn('response_id', result)

    def test_try_openai_fallback_emergency_send_error(self):
        handler = self.handler
        handler._create_fallback_prompt = Mock(return_value='prompt')
        handler.embedding_manager.generate_embedding = Mock(side_effect=Exception('embedding error'))
        handler.acs_service.send_text_message = Mock(side_effect=Exception('send error'))
        result = handler._try_openai_fallback('+123', 'msg', 'general', {})
        self.assertFalse(result['success'])
        self.assertIn('Fallback error', result['error_message']) 