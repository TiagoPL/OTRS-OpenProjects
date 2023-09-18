def work_package(titulo, proprietario, id, ticket):
  return """{
  "_type": "WorkPackage",
  "_links": {
    "self": {
      "href": "/api/v3/work_packages/1528",""" + f"""
      "title": "Chamado de Suporte - {titulo}"
    """ + """},
    "schema": {
      "href": "/api/v3/work_packages/schemas/11-2"
    },
    "responsible": {""" + f"""
      "href": "/api/v3/users/7",
      "title": "samuel.pereira"
    """ + """},
    "assignee": {""" + f"""
      "href": "/api/v3/users/{id}",
      "title": "{proprietario}"
    """ + """}
  },""" + f"""
  "subject": "Chamado de Suporte - {titulo}",""" + """
  "description": {
    "format": "markdown",""" + f"""
    "raw": "https://clientes.domain.com.br/otrs/index.pl?Action=AgentTicketZoom;TicketID={ticket}",
    "html": "<p>https://clientes.domain.com.br/otrs/index.pl?Action=AgentTicketZoom;TicketID={ticket}</p>" """ + """
  }
}"""
