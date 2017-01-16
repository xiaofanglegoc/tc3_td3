# TD3/Q4-1.py

# pour le serveur web
import socketserver

# pour la gestion des noms de fichiers
import os

# pour l'accès base de données
import sqlite3

# pour le tracé graphique
import matplotlib.pyplot as plt
from random import random

# pour la fonction d'interpolation
import numpy as np
from scipy import interpolate


#
# Définition du nouveau handler
#
import generic 

class RequestHandler(generic.RequestHandler):

  # on utilise le nom de fichier pour identifier le serveur
  server_version = 'TD3/'+os.path.basename(__file__)+'/0.1'

  #
  # initialisation noms du fichier image
  #
  def init_vars(self):
    generic.RequestHandler.init_vars(self)
    self.imagename = 'images/{}.png'.format('_'.join(self.path_info))
    self.imagepath = 'client/{}'.format(self.imagename)

  #
  # On surcharge la méthode qui traite les requêtes GET
  #
  def do_GET(self):

    # on initialise nos variables d'instance
    self.init_vars()

    # le chemin d'accès commence par /lignes
    if len(self.path_info) > 0 and self.path_info[0] == 'lignes':
      self.send_trains()

    # le chemin d'accès commence par /ponctualite
    elif len(self.path_info) > 1 and self.path_info[0] == 'ponctualite' :

      # si le fichier existe on le renvoie, sinon 404
      if os.path.isfile(self.imagepath):
        self.send_image()
      else:
        self.send_error(404)
    
    # ou pas...
    else:
      self.send_static()

  #
  # Autre verbes HTTP
  #
  def do_POST(self):
    self.init_vars()
    if len(self.path_info) > 1 and self.path_info[0] == 'ponctualite' :
      if not os.path.isfile(self.imagepath):
         self.create_ponctualite()
      self.send_image()
    else:
      self.send_error(400)
      
  def do_PUT(self):
    self.init_vars()
    if len(self.path_info) > 1 and self.path_info[0] == 'ponctualite' :
      self.create_ponctualite()
      self.send_image()
    else:
      self.send_error(400)

  def do_DELETE(self):
    self.init_vars()
    if len(self.path_info) > 1 and self.path_info[0] == 'ponctualite' :
      if os.path.isfile(self.imagepath):
        os.remove(self.imagepath)
      self.send('')
    else:
      self.send_error(400)

  #
  # On envoie un document avec la liste des lignes
  #
  def send_trains(self):

    conn = sqlite3.connect('sncf.sqlite')
    c = conn.cursor()
    c.execute("SELECT DISTINCT c.hexadecimal, p.code_ligne, p.nom_ligne " +\
              "FROM ponctualite_transilien AS p, couleur_transilien as c " +\
              "WHERE c.code_ligne = p.code_ligne " +\
              "ORDER BY p.code_ligne")
    r = c.fetchall()

    row1 = '<tr><td colspan=2>code</td><td>ligne</td><tr>'
    rows = ['<tr><td style="background-color: {}">&nbsp;</td><td>{}</td><td>{}</td></tr>'.format(*a) for a in r]
    html = '<table>{}\n{}</table>'.format(row1,'\n'.join(rows))

    headers = [('Content-Type','text/html;charset=utf-8')]
    self.send(html,headers)


  #
  # On renvoie la balise image
  #
  def send_image(self):
    headers = [('Content-Type','text/html;charset=utf-8')]
    html = '<img src="{}?{}" alt="{}">'.format(self.imagename,random(),' '.join(self.path_info))
    self.send(html,headers)


  #
  # Création d'un graphique de ponctualité (cf. TD1)
  #
  def create_ponctualite(self):

    # connexion sqlite
    conn = sqlite3.connect('sncf.sqlite')
    c = conn.cursor()
    
    # liste des lignes de RER avec leur code couleur
    condition_code_ligne = ("= '{}'".format(self.path_info[2]) if len(self.path_info) > 2 else "LIKE '%'")
    c.execute("SELECT DISTINCT ponctualite_transilien.code_ligne, couleur_transilien.hexadecimal \
           FROM ponctualite_transilien, couleur_transilien \
           WHERE ponctualite_transilien.code_ligne = couleur_transilien.code_ligne \
           AND ponctualite_transilien.type_ligne = '{}' \
           AND ponctualite_transilien.code_ligne {} \
           ORDER BY ponctualite_transilien.code_ligne".format(self.path_info[1],condition_code_ligne))
    lignes = c.fetchall()

    # on n'a rien trouvé
    if not len(lignes):
      self.send_error(400)
      return

    # configuration du tracé
    plt.figure(figsize=(18,6))
    plt.ylim(65,100)
    plt.grid(True)

    # boucle sur les lignes
    for l in (lignes):
      c.execute("SELECT ponctualite_transilien.* \
               FROM ponctualite_transilien \
               WHERE ponctualite_transilien.code_ligne = ? \
               ORDER BY annee, mois",l[0])
      a = c.fetchall()

      # il y a une valeur manquante pour le RER B
      x = [n for n in range(len(a)) if not a[n][7] == '']
      y = [r[7] for r in a if not r[7] == '']

      # interpolation spline
      spl = interpolate.splrep(x, y, s=0)
      x2 = [n/10 for n in range(10*(len(a)-1)+1)]
      y2 = interpolate.splev(x2, spl, der=0)

      # tracé de la courbe de régularité
      plt.plot(x2,y2,linewidth=2,color=l[1], label=('RER ' if self.path_info[1] == 'RER' else 'ligne ')+l[0])
      plt.plot(x,y,linewidth=0,marker='s',markeredgecolor='w',markerfacecolor=l[1],markersize=10)
    
    # configuration du tracé (titre, grille)
    plt.grid(which='major', color='#888888', linestyle='-')
    plt.grid(which='minor',axis='x', color='#888888', linestyle=':')
    print(self.path_info,len(self.path_info))
    plt.title('Ponctualité {} {} {} (en %)'.format(
      'de la ligne' if len(self.path_info) > 2 else 'des lignes',
      self.path_info[1],
      self.path_info[2] if len(self.path_info) > 2 else ''),fontsize=16)

    # configuration de l'axe du temps
    mois = ['Jan','Fév','Mar','Avr', 'Mai', 'Juin', 'Juil', 'Août', 'Sept', 'Oct', 'Nov', 'Déc']
    xticks = [n*4 for n in range(int(len(a)/4))]
    xlabels = ['{} {}'.format(mois[r[2]-1], r[1]) for r in [a[t] for t in xticks]]

    plt.xlim(0,len(a)-1)
    ax = plt.subplot(111)
    ax.set_xticks(xticks)
    ax.set_xticks(x, minor=True)
    ax.set_xticklabels(xlabels, fontsize=12)

    # légende
    plt.legend(loc='lower left')

    # création du fichier
    plt.savefig(self.imagepath)

    
#
# Instanciation et lancement du serveur
#
httpd = socketserver.TCPServer(("", 8080), RequestHandler)
httpd.serve_forever()
