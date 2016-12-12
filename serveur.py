# TD3/serveur.py

import http.server
import socketserver
from urllib.parse import urlparse, parse_qs


# définition du handler
class RequestHandler(http.server.SimpleHTTPRequestHandler):

  # sous-répertoire racine des documents statiques
  static_dir = '/client'

  # version du serveur
  server_version = 'TD3/serveur.py/0.1'

  # on surcharge la méthode qui traite les requêtes GET
  def do_GET(self):
    self.init_params()

    # prénom et nom dans le chemin d'accès
    if self.path_info[0] == 'coucou':
      self.send_html('<p>Bonjour {} {}</p>'.format(*self.path_info[1:]))

    # prénom et nom dans la chaîne de requête
    elif self.path_info[0] == "toctoc":
      self.send_html('<p>Bonjour {} {}</p>'.format(self.params['Prenom'][0],self.params['Nom'][0]))

    # requête générique
    elif self.path_info[0] == "service":
      self.send_html('<p>Path info : <code>{}</p><p>Chaîne de requête : <code>{}</code></p>' \
          .format('/'.join(self.path_info),self.query_string));

    else:
      self.send_static()


  # méthode pour traiter les requêtes HEAD
  def do_HEAD(self):
      self.send_static()


  # méthode pour traiter les requêtes POST
  def do_POST(self):
    self.init_params()

    # prénom et nom dans la chaîne de requête dans le corps
    if self.path_info[0] == "toctoc":
      self.send_html('<p>Bonjour {} {}</p>'.format(self.params['Prenom'][0],self.params['Nom'][0]))

    # requête générique
    elif self.path_info[0] == "service":
      self.send_html(('<p>Path info : <code>{}</code></p><p>Chaîne de requête : <code>{}</code></p>' \
          + '<p>Corps :</p><pre>{}</pre>').format('/'.join(self.path_info),self.query_string,self.body));

    else:
      self.send_error(405)


  # on envoie le document statique demandé
  def send_static(self):

    # on modifie le chemin d'accès en insérant le répertoire préfixe
    self.path = self.static_dir + self.path

    # on calcule le nom de la méthode parent à appeler (do_GET ou do_HEAD)
    # à partir du verbe HTTP (GET ou HEAD)
    method = 'do_{}'.format(self.command)

    # on traite la requête via la classe parent
    getattr(http.server.SimpleHTTPRequestHandler,method)(self)


  # on envoie un document html dynamique
  def send_html(self,content):
     headers = [('Content-Type','text/html;charset=utf-8')]
     html = '<!DOCTYPE html><title>{}</title><meta charset="utf-8">{}' \
         .format(self.path_info[0],content)
     self.send(html,headers)


  # on envoie la réponse
  def send(self,body,headers=[]):
     encoded = bytes(body, 'UTF-8')

     self.send_response(200)

     [self.send_header(*t) for t in headers]
     self.send_header('Content-Length',int(len(encoded)))
     self.end_headers()

     self.wfile.write(encoded)


  # on analyse la requête pour initialiser nos paramètres
  def init_params(self):
    # analyse de l'adresse
    info = urlparse(self.path)
    self.path_info = info.path.split('/')[1:]
    self.query_string = info.query
    self.params = parse_qs(info.query)

    # récupération du corps
    length = self.headers.get('Content-Length')
    ctype = self.headers.get('Content-Type')
    if length:
      self.body = str(self.rfile.read(int(length)),'utf-8')
      if ctype == 'application/x-www-form-urlencoded' : 
        self.params = parse_qs(self.body)
    else:
      self.body = ''

    print(length,ctype,self.body, self.params)


# instanciation et lancement du serveur
httpd = socketserver.TCPServer(("", 8080), RequestHandler)
httpd.serve_forever()
