 Esta API tem como função automatizar a criação de tarefas no 4Projects de chamados abertos no OTRS clientes.

 Ela funciona em 3 etapas:
 - Acessa o OTRS Clientes, coleta as informações de todos os tickets com o status "Aberto", que são tickets que foram pêgos por um colaborador, após coletar as informações do ticket, ele altera o estado do mesmo para "Em execução".
 - Com os dados do chamado, a API se conecta no 4Projects, e cria uma tarefa relacionada aquele chamado, já passando informações de fila e responsável.
 - Por fim ela se conecta no RocketChat e notifica o funcionário de que uma nova tarefa foi criada e designada à ele no 4Projects.

  Em caso de falha devido a dependencias de configuração no projects (Usuario ou projeto não criado por exemplo), o gerentes (Samuel e Pollyana) são notificados via RocketChat de forma privada; Se a aplicação em si falhar uma notificação será enviada no chat no canal "Infraestrutura".
  
  O arquivo "GenericTicketConnectorREST.yml" neste repositorio é necessário no OTRS para que ele possibilite a conexão via API.

 A API utiliza uma conta de serviço chamada "svc_otrs_projects" para seus acessos, sua senha está no sysPAss com o mesmo nome.

 Existe uma job no rundeck que executa a API a cada 30min:
 https://rundeck.domain.com.br/project/Infraestrutura/job/show/6597c36f-b19e-4838-bed2-456dc7814483

 Para mais detalhes sobre o funcionamento da aplicação, o arquivo app.py está todo comentado.
