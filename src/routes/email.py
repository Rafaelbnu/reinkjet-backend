from flask import Blueprint, request, jsonify
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import os

email_bp = Blueprint('email', __name__)

# Configurações de email (em produção, usar variáveis de ambiente)
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
EMAIL_USER = os.getenv('EMAIL_USER', 'sistema@reinkjet.com.br')
EMAIL_PASSWORD = os.getenv('EMAIL_PASSWORD', 'senha_app')

# Emails de destino para cada serviço
EMAIL_DESTINATIONS = {
    'manutencao': 'manutencao@reinkjet.com.br',
    'locacao': 'locacao@reinkjet.com.br',
    'suprimentos': 'vendas@reinkjet.com.br',
    'geral': 'contato@reinkjet.com.br'
}

def send_email(to_email, subject, body):
    """Função para enviar email"""
    try:
        # Criar mensagem
        msg = MIMEMultipart()
        msg['From'] = EMAIL_USER
        msg['To'] = to_email
        msg['Subject'] = subject
        
        # Adicionar corpo do email
        msg.attach(MIMEText(body, 'html'))
        
        # Conectar ao servidor SMTP
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(EMAIL_USER, EMAIL_PASSWORD)
        
        # Enviar email
        text = msg.as_string()
        server.sendmail(EMAIL_USER, to_email, text)
        server.quit()
        
        return True
    except Exception as e:
        print(f"Erro ao enviar email: {str(e)}")
        return False

@email_bp.route('/send-ticket-notification', methods=['POST'])
def send_ticket_notification():
    """Enviar notificação de novo chamado técnico"""
    try:
        data = request.get_json()
        
        # Dados do chamado
        ticket_id = data.get('ticket_id')
        customer_name = data.get('customer_name')
        equipment = data.get('equipment')
        issue_type = data.get('issue_type')
        description = data.get('description')
        priority = data.get('priority', 'Média')
        
        # Email de destino
        to_email = EMAIL_DESTINATIONS['manutencao']
        
        # Assunto
        subject = f"Novo Chamado Técnico #{ticket_id} - {priority}"
        
        # Corpo do email
        body = f"""
        <html>
        <body>
            <h2>Novo Chamado Técnico Aberto</h2>
            <p><strong>Chamado:</strong> #{ticket_id}</p>
            <p><strong>Cliente:</strong> {customer_name}</p>
            <p><strong>Equipamento:</strong> {equipment}</p>
            <p><strong>Tipo de Problema:</strong> {issue_type}</p>
            <p><strong>Prioridade:</strong> {priority}</p>
            <p><strong>Descrição:</strong></p>
            <p>{description}</p>
            <p><strong>Data/Hora:</strong> {datetime.now().strftime('%d/%m/%Y %H:%M')}</p>
            
            <hr>
            <p><em>Este email foi gerado automaticamente pelo sistema da Reinkjet.</em></p>
        </body>
        </html>
        """
        
        # Enviar email
        if send_email(to_email, subject, body):
            return jsonify({'success': True, 'message': 'Email enviado com sucesso'})
        else:
            return jsonify({'success': False, 'message': 'Erro ao enviar email'}), 500
            
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@email_bp.route('/send-quote-request', methods=['POST'])
def send_quote_request():
    """Enviar solicitação de orçamento"""
    try:
        data = request.get_json()
        
        # Dados da solicitação
        service_type = data.get('service_type', '').lower()
        customer_name = data.get('customer_name')
        company = data.get('company')
        phone = data.get('phone')
        email = data.get('email')
        message = data.get('message', '')
        
        # Determinar email de destino baseado no tipo de serviço
        if 'outsourcing' in service_type or 'locacao' in service_type or 'locação' in service_type:
            to_email = EMAIL_DESTINATIONS['locacao']
            service_name = 'Outsourcing/Locação'
        elif 'suprimento' in service_type or 'cartucho' in service_type or 'toner' in service_type:
            to_email = EMAIL_DESTINATIONS['suprimentos']
            service_name = 'Suprimentos'
        elif 'manutencao' in service_type or 'manutenção' in service_type or 'suporte' in service_type:
            to_email = EMAIL_DESTINATIONS['manutencao']
            service_name = 'Manutenção'
        else:
            to_email = EMAIL_DESTINATIONS['geral']
            service_name = 'Geral'
        
        # Assunto
        subject = f"Nova Solicitação de Orçamento - {service_name}"
        
        # Corpo do email
        body = f"""
        <html>
        <body>
            <h2>Nova Solicitação de Orçamento</h2>
            <p><strong>Tipo de Serviço:</strong> {service_name}</p>
            <p><strong>Cliente:</strong> {customer_name}</p>
            <p><strong>Empresa:</strong> {company}</p>
            <p><strong>Telefone:</strong> {phone}</p>
            <p><strong>E-mail:</strong> {email}</p>
            
            {f'<p><strong>Mensagem:</strong></p><p>{message}</p>' if message else ''}
            
            <p><strong>Data/Hora:</strong> {datetime.now().strftime('%d/%m/%Y %H:%M')}</p>
            
            <hr>
            <p><em>Solicitação enviada através do site da Reinkjet.</em></p>
        </body>
        </html>
        """
        
        # Enviar email
        if send_email(to_email, subject, body):
            return jsonify({'success': True, 'message': 'Solicitação enviada com sucesso'})
        else:
            return jsonify({'success': False, 'message': 'Erro ao enviar solicitação'}), 500
            
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@email_bp.route('/send-contact-form', methods=['POST'])
def send_contact_form():
    """Enviar formulário de contato"""
    try:
        data = request.get_json()
        
        # Dados do formulário
        name = data.get('name')
        email = data.get('email')
        phone = data.get('phone', '')
        subject = data.get('subject', 'Contato via Site')
        message = data.get('message')
        
        # Email de destino
        to_email = EMAIL_DESTINATIONS['geral']
        
        # Assunto
        email_subject = f"Contato via Site - {subject}"
        
        # Corpo do email
        body = f"""
        <html>
        <body>
            <h2>Novo Contato via Site</h2>
            <p><strong>Nome:</strong> {name}</p>
            <p><strong>E-mail:</strong> {email}</p>
            {f'<p><strong>Telefone:</strong> {phone}</p>' if phone else ''}
            <p><strong>Assunto:</strong> {subject}</p>
            <p><strong>Mensagem:</strong></p>
            <p>{message}</p>
            <p><strong>Data/Hora:</strong> {datetime.now().strftime('%d/%m/%Y %H:%M')}</p>
            
            <hr>
            <p><em>Mensagem enviada através do site da Reinkjet.</em></p>
        </body>
        </html>
        """
        
        # Enviar email
        if send_email(to_email, email_subject, body):
            return jsonify({'success': True, 'message': 'Mensagem enviada com sucesso'})
        else:
            return jsonify({'success': False, 'message': 'Erro ao enviar mensagem'}), 500
            
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@email_bp.route('/test-email', methods=['GET'])
def test_email():
    """Testar configuração de email"""
    try:
        test_subject = "Teste de Configuração - Sistema Reinkjet"
        test_body = """
        <html>
        <body>
            <h2>Teste de Configuração de Email</h2>
            <p>Este é um email de teste para verificar se o sistema está funcionando corretamente.</p>
            <p><strong>Data/Hora:</strong> {}</p>
        </body>
        </html>
        """.format(datetime.now().strftime('%d/%m/%Y %H:%M'))
        
        # Enviar para email geral
        if send_email(EMAIL_DESTINATIONS['geral'], test_subject, test_body):
            return jsonify({'success': True, 'message': 'Email de teste enviado com sucesso'})
        else:
            return jsonify({'success': False, 'message': 'Erro ao enviar email de teste'}), 500
            
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

