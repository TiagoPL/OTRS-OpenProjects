import os #Usado pra pegar a variável de ambiente onde a senha do usuario do OTRS foi armazenada (via k8s secrets).
import json #Usado pra formatar as informações a serem enviadas pro Projects.
import requests #Usado pra enviar uma mensagem através do webhook do rocketchat pros usuarios que tiveram pacotes abertos.
from work_package_payload import work_package #Arquivo contendo o layout do arquivo a ser enviado pro Projects.
import urllib3 #Usado para suprimir mensagens de falta de ssl na conexão do webhook.
from pyotrs import Client #Utilizado pra criar uma conexão com o OTRS.
from pyotrs.lib import TICKET_CONNECTOR_CONFIG_DEFAULT #Utilizado pra configurar a conexão com o OTRS.
from pyopenproject.openproject import OpenProject #Utilizado pra criar uma conexão com o Projects.
from pyopenproject.model.work_package import WorkPackage #Utilizado pra formatar as informações a serem enviadas pro Projects.
from flask import Flask #Utilizado pra criar a API por onde a aplicação será acessada.


urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning) #Suprime mensagens sobre a segurança do webhook.
app = Flask(__name__)

@app.route("/")
def index():
    # A API PODE SER DIVIDIDA EM 3 PARTES, ELA SE CONECTA NO OTRS PRA COLETAR AS INFORMAÇÕES DOS CHAMADOS, DEPOIS SE CONECTA NO PROJECTS PRA CRIAR AS
    # TAREFAS E POR FIM SE CONECTA NO ROCKETCHAT PRA NOTIFICAR AS PESSOAS RELACIONADAS AS TAREFAS ABERTAS OU A GERENCIA SE NECESSÁRIO.

# PARTE 01/03 [OTRS]: =========================================================

    #Configuramos a conexão com o OTRS:
    TICKET_CONNECTOR_CONFIG = TICKET_CONNECTOR_CONFIG_DEFAULT
    TICKET_CONNECTOR_CONFIG['Config']['TicketSearch']['RequestMethod'] = 'POST'
    TICKET_CONNECTOR_CONFIG['Config']['TicketSearch']['Route'] = '/TicketSearch'

    #Iniciamos a conexão com o OTRS:
    user_password = os.environ.get('OTRS_PASSWORD')

    client = Client("https://clientes.domain.com.br/", "svc_otrs_projects", user_password, webservice_config_ticket=TICKET_CONNECTOR_CONFIG)
    client.session_create()
    usuarios_a_notificar = []

    #Coletamos todos os chamados com determinado estado no OTRS:
    novos_chamados = (client.ticket_search(States=["Aberto"]))

    #Iniciamos um loop, coletando as informações relevantes de cada chamado obtido:
    for chamado in novos_chamados:
        ticket = client.ticket_get_by_id(chamado)
        ticket_title = ticket.field_get("Title")
        ticket_fila = ticket.field_get("Queue")
        ticket_owner = ticket.field_get("Owner")

        #Caso o chamado pertença ao "fabio.schmidt", seguimos para o próximo loop sem dar continuidade a este. É uma exceção.
        if ticket_owner == "fabio.schmidt":
            continue

# PARTE 02/03 [PROJECTS]: =====================================================  

        #Iniciamos a conexão com o Projects (ainda dentro do loop):
        op = OpenProject(url="https://projetos.domain.com.br/", api_key="123")

        #Checamos se a fila em questão já possui um projeto criado no 4Projects:
        project_found = False
        projects = op.get_project_service().find_all()
        for item in projects:
            if item.customField28 == ticket_fila:
                project_found = True
                project_id = item.id
                project_name = item.name
                break

        #Se o projeto NÃO for encontrado no projects, enviamos uma mensagem no rocketchat para a gerencia:
        gerencia = ["123", "123"]
        if project_found == False:
            for gerente in gerencia:
                headers = {}
                json_data = {
                    'channel': '@{gerente}',
                    'username': '4SecBot',
                    'avatar': 'https://blog.domain.com.br/wp-content/uploads/2022/10/4secbot.png',
                    'text': f"Uma tarefa vinda do OTRS, fila '{ticket_fila}', não pôde ser criada no Projects pois um projeto com esse customField não foi encontrado.'"
                            }
            
                requests.post('https://chat.4linux.com.br/hooks/123/123', headers=headers, json=json_data, verify=False)
                print(f'Projeto "{ticket_fila}" não encontrado, notificando os gestores via rocketchat.')
                continue
            continue

        #Se o projeto FOR encontrado no projects, criamos uma classe contendo as informações do projeto ao qual a tarefa será atribuido:
        class TargetProject():
            def __init__(self):
                self.name = project_name
                self.id = project_id

        #Coletamos as informações dos usuarios existentes no Projects:
        owner_info = op.get_user_service().find_all()

        #Checamos se o usuario do OTRS ao qual o ticket pertence existe no Projects, e qual o seu ID:
        user_found = False
        for user in owner_info:
            if user.login == ticket_owner:
                ticket_owner_id = user.id
                print(f"Usuario {ticket_owner} encontrado! Seguindo para o 4Projects... \n")
                user_found = True
                break

        #Se o usuario não for encontrado, enviamos uma mensagem para a gerencia no RocketChat:
        if user_found == False:
            for gerente in gerencia:
                headers = {}
                json_data = {
                    'channel': f'@{gerente}',
                    'username': '4SecBot',
                    'avatar': 'https://blog.domain.com.br/wp-content/uploads/2022/10/4secbot.png',
                    'text': f"Uma tarefa vinda do OTRS não pôde ser criada no projeto '{project_name}' porque o usuário '{ticket_owner}' não é membro deste projeto."
                            }
            
                requests.post('https://chat.domain.com.br/hooks/123/123', headers=headers, json=json_data, verify=False)
                print(f'Membro "{ticket_owner}" não encontrado no projeto "{project_name}", notificando os gestores via rocketchat.')
            continue

        #Se o usuario for encontrado, enviamos o payload para o Projects para que a tarefa seja criada e atribuída ao usuario correto.
        #Para tal, primeiro coletamos as informações de todas as tarefas nesse projeto pra não criarmos uma tarefa duplicada:
        tarefas = op.get_project_service().find_work_packages(project=TargetProject())

        tarefa_encontrada = False
        for tarefa in tarefas:
            if tarefa.subject == f"Chamado de Suporte - {ticket_title}":
                tarefa_encontrada = True
                print("Tarefa em questão já existe no 4Projects, pulando.")
                break
        
        #Se a tarefa ainda não existir no Projects, criamos uma nova a partir do arquivo "work_package_payload.py" no diretório da aplicação:
        if tarefa_encontrada == False:
            usuarios_a_notificar.append(ticket_owner)

            with open("work_package.json", "w") as w:
                w.write(work_package(ticket_title, ticket_owner, ticket_owner_id, chamado))

            with open("work_package.json", "r") as f:
                payload = WorkPackage(json.load(f))

            #Enviamos o payload para o Projects para que a tarefa seja criada e atribuída ao usuario correto.
            op.get_project_service().create_work_package(project=TargetProject(), work_package=payload)

        #Por fim, alteramos o estado do chamado para que a API não o pegue novamente na próxima execução:
        client.ticket_update(chamado, State="Execução")

# PARTE 03/03 [ROCKETCHAT]: ===================================================  

    #Enviamos uma mensagem no rocketchat pra cada usuario que teve uma nova tarefa recebida:
    for usuario in usuarios_a_notificar:

        headers = {}
        json_data = {
            'channel': f'@{usuario}',
            'username': '4SecBot',
            'avatar': 'https://blog.domain.com.br/wp-content/uploads/2022/10/4secbot.png',
            'text': "Uma nova tarefa vinda do OTRS Clientes foi criada e destinada a voce no 4Projects, por favor verifique-a em: https://projetos.4linux.com.br/my/page"
                    }
        
        requests.post('https://chat.domain.com.br/hooks/123/123', headers=headers, json=json_data, verify=False)

    #Respondemos o chamado pela API com o resultado(return -> aparece no navegador pro usuario) e também anotamos o resultado no terminal(print -> aparece no terminal pra logs):
    if usuarios_a_notificar != []:
        print(f"\nAplicação executada com sucesso, os seguintes usuarios foram notificados de novas tarefas via RocketChat: {usuarios_a_notificar}")
        return f"Aplicação executada com sucesso, os seguintes usuarios foram notificados de novas tarefas via RocketChat: {usuarios_a_notificar}"
    else:
        print(f"\nAplicação executada com sucesso, nenhuma nova tarefa criada.")
        return "Aplicação executada com sucesso, nenhuma nova tarefa criada."
