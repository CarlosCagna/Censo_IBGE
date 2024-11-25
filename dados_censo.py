# -*- coding: utf-8 -*-
"""
/***************************************************************************
 DadosCenso
                                 A QGIS plugin
 baixa os setores dos censos do IBGE juntando com os resultados por setores escolhidos, os dados são baixados do https://ftp.ibge.gov.br/.
 Generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/
                              -------------------
        begin                : 2021-07-19
        git sha              : $Format:%H$
        copyright            : (C) 2021 by Carlos Eduardo Cagna
        email                : carlos_cagna@yahoo.com.br
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""
from qgis.PyQt.QtCore import *
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction, QProgressBar
from qgis.core import *
# Initialize Qt resources from file resources.py
from .resources import *
# Import the code for the dialog
from .dados_censo_dialog import DadosCensoDialog
import os.path
import os
import shutil
import requests
import zipfile
import ast
import processing
import subprocess
import webbrowser

lista_estados = {'':'','Acre':('AC', '12') , 'Alagoas':('AL','27')  , 'Amapá':('AP', '16') , 'Amazonas':('AM', '13') , 'Bahia':('BA', '29') , 'Ceará':('CE', '23') , 'Espírito Santo':('ES', '32'), 'Distrito Federal':('DF', '53'), 'Goiás':('GO', '52'), 'Maranhão':('MA', '21') , 'Mato Grosso':('MT', '51') , 'Mato Grosso do Sul':('MS', '50') , 'Minas Gerais':('MG', '31') , 'Pará':('PA', '15') , 'Paraíba':('PB', '25') , 'Paraná':('PR', '41') , 'Pernambuco':('PE', '26') , 'Piauí':('PI', '22') , 'Rio de Janeiro':('RJ', '33') , 'Rio Grande do Norte':('RN', '24') , 'Rio Grande do Sul':('RS', '43') , 'Rondônia':('RO', '11') , 'Roraima':('RR', '14') , 'Santa Catarina':('SC', '42') , 'São Paulo - exceto capital':('SP_Exceto_Capital', '35') , 'São Paulo - Capital':('SP_Capital', '35'),'Sergipe':('SE', '28') , 'Tocantins':('TO', '17')}		 
lista_municipios = {}
class DadosCenso:
    """QGIS Plugin Implementation."""

    def __init__(self, iface):
        """Constructor.

        :param iface: An interface instance that will be passed to this class
            which provides the hook by which you can manipulate the QGIS
            application at run time.
        :type iface: QgsInterface
        """
        # Save reference to the QGIS interface
        self.iface = iface
        # initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__)
        # initialize locale
        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(
            self.plugin_dir,
            'i18n',
            'DadosCenso_{}.qm'.format(locale))

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)
            QCoreApplication.installTranslator(self.translator)

        # Declare instance attributes
        self.actions = []
        self.menu = self.tr(u'&Censo IBGE')

        # Check if plugin was started the first time in current QGIS session
        # Must be set in initGui() to survive plugin reloads
        self.first_start = None

    # noinspection PyMethodMayBeStatic
    def tr(self, message):
        """Get the translation for a string using Qt translation API.

        We implement this ourselves since we do not inherit QObject.

        :param message: String for translation.
        :type message: str, QString

        :returns: Translated version of message.
        :rtype: QString
        """
        # noinspection PyTypeChecker,PyArgumentList,PyCallByClass
        return QCoreApplication.translate('DadosCenso', message)

    def add_action(
        self,
        icon_path,
        text,
        callback,
        enabled_flag=True,
        add_to_menu=True,
        add_to_toolbar=True,
        status_tip=None,
        whats_this=None,
        parent=None):
        """Add a toolbar icon to the toolbar.

        :param icon_path: Path to the icon for this action. Can be a resource
            path (e.g. ':/plugins/foo/bar.png') or a normal file system path.
        :type icon_path: str

        :param text: Text that should be shown in menu items for this action.
        :type text: str

        :param callback: Function to be called when the action is triggered.
        :type callback: function

        :param enabled_flag: A flag indicating if the action should be enabled
            by default. Defaults to True.
        :type enabled_flag: bool

        :param add_to_menu: Flag indicating whether the action should also
            be added to the menu. Defaults to True.
        :type add_to_menu: bool

        :param add_to_toolbar: Flag indicating whether the action should also
            be added to the toolbar. Defaults to True.
        :type add_to_toolbar: bool

        :param status_tip: Optional text to show in a popup when mouse pointer
            hovers over the action.
        :type status_tip: str

        :param parent: Parent widget for the new action. Defaults None.
        :type parent: QWidget

        :param whats_this: Optional text to show in the status bar when the
            mouse pointer hovers over the action.

        :returns: The action that was created. Note that the action is also
            added to self.actions list.
        :rtype: QAction
        """

        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)

        if status_tip is not None:
            action.setStatusTip(status_tip)

        if whats_this is not None:
            action.setWhatsThis(whats_this)

        if add_to_toolbar:
            # Adds plugin icon to Plugins toolbar
            self.iface.addToolBarIcon(action)

        if add_to_menu:
            self.iface.addPluginToWebMenu(
                self.menu,
                action)

        self.actions.append(action)

        return action

    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI."""

        icon_path = ':/plugins/dados_censo/icon.png'
        self.add_action(
            icon_path,
            text=self.tr(u'Censo IBGE'),
            callback=self.run,
            parent=self.iface.mainWindow())

        # will be set False in run()
        self.first_start = True

    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""
        for action in self.actions:
            self.iface.removePluginWebMenu(
                self.tr(u'&Censo IBGE'),
                action)
            self.iface.removeToolBarIcon(action)

    def limpa_dados(self):
        #self.dlg.estadoComboBox.setCurrentIndex(0) 
        #self.dlg.municipioComboBox.setCurrentIndex(0) 
        self.dlg.tabelaComboBox.setCurrentIndex(0) 
        self.dlg.listBox_disponiveis.clear() 
        self.dlg.listBox_selecionados.clear() 
        self.dlg.textBrowser_soma.clear() 
        self.dlg.textBrowser_divi.clear() 

    def baixa_dados_estado(self, UF, UF_codigo, estado):
        def download_file(url, folder_name):
            local_filename = url.split('/')[-1]
            path = os.path.join("{}/{}".format(folder_name, local_filename))
            with requests.get(url, stream=True, verify=False) as r:
                with open(path, 'wb') as f:
                    shutil.copyfileobj(r.raw, f)
            progress.setValue(self.i + 1)
            self.i = self.i + 1
            return local_filename

        def baixa_setores(UF, UF_codigo, pasta):
            dict_arquivos = {'_distritos.zip':'DSE250GC_SIR.shp', '_municipios.zip':'MUE250GC_SIR.shp', '_subdistritos.zip':'SDE250GC_SIR.shp', '_setores_censitarios.zip':'SEE250GC_SIR.shp'}
            for item in dict_arquivos.keys():
                if not os.path.isfile(pasta+'/'+UF_codigo+dict_arquivos[item]):  
                    print(pasta+'/'+UF_codigo+dict_arquivos[item])
                    url= u"https://geoftp.ibge.gov.br/organizacao_do_territorio/malhas_territoriais/malhas_de_setores_censitarios__divisoes_intramunicipais/censo_2010/setores_censitarios_shp/{0}/{0}{1}".format(UF.lower(), item)
                    print(url)
                    download_file(url, pasta)
                    with zipfile.ZipFile(pasta+'/'+UF.lower()+item, 'r') as zip_ref:
                        zip_ref.extractall(pasta)     
                    os.remove(pasta+'/'+UF.lower()+item)        

        def baixa_dados(UF, pasta, estado):   
            if 'Exceto_Capital'  in UF:
                UF2 = 'SP2'
            elif 'Capital'  in UF:
                UF2 = 'SP1'
            else:
                UF2 = UF
            print('UF2', UF2)
            arquivo = '_20231030'            
            caminho_planilha = '{0}/dados_IBGE/Base informaçoes setores2010 universo {1}/CSV/{2}_{3}.csv'.format(self.plugin_dir, UF,  'Basico', UF2)        
            print(caminho_planilha)
            if not os.path.isfile(caminho_planilha):    
                url= "https://ftp.ibge.gov.br/Censos/Censo_Demografico_2010/Resultados_do_Universo/Agregados_por_Setores_Censitarios/{0}{1}.zip".format(UF, arquivo)               
                print(url)
                download_file(url, pasta)   
                #print(pasta+'/'+UF+arquivo+'.zip')
                with zipfile.ZipFile(pasta+'/'+UF+arquivo+'.zip', 'r') as zip_ref:
                    zip_ref.extractall(pasta)        
                os.remove(pasta+'/'+UF+arquivo+'.zip') 
                
        def arruma_pastas(UF, pasta, estado):
            caminho_planilha = '{0}/dados_IBGE/Base informaçoes setores2010 universo {1}/CSV/{2}_{1}.csv'.format(self.plugin_dir, UF,  'Basico')        
            if not os.path.isfile(caminho_planilha):          
                if UF == 'ES' or UF == 'TO' or UF == 'SP_Capital':
                    if UF == 'TO':
                        os.rename(pasta+"/Base informacoes setores2010 universo TO", pasta+"/Base informaçoes setores2010 universo TO")    
                    arquivo = 'Base informaçoes setores2010 universo '+ UF
                    shutil.move((pasta+"/"+arquivo), (pasta+'/'+UF+'/'+arquivo)) 
                    
                if UF == 'SP_Capital':
                    arquivo = 'PE_20171016'
                    shutil.move((pasta+"/"+arquivo+"/"+UF), (pasta+"/"+UF)) 
                    os.rmdir(pasta+"/"+arquivo)    
                   
                elif UF == 'RS':
                    arquivo = 'RS_20150527'
                    shutil.move((pasta+"/"+arquivo+"/"+UF), (pasta+"/"+UF))
                    os.rmdir(pasta+"/"+arquivo) 
                    
                elif UF == 'SP_Exceto_Capital':
                    arquivo = 'SP Exceto Capital'
                    shutil.move((pasta+"/"+arquivo), (pasta+"/"+UF))
                    #os.rmdir(pasta+"/"+arquivo) 
                    os.rename(pasta+"/"+UF+"/Base informaçoes setores2010 universo SP_Exceto_Capital", pasta+"/"+UF+"/Base informaçoes setores2010 universo "+UF)
                    
                if UF == 'SP_Capital' or UF == 'SP_Exceto_Capital':
                    pasta_alvo = pasta+"/"+UF+"/Base informaçoes setores2010 universo "+UF+"/"+"CSV"
                    for filename in os.listdir(pasta_alvo):
                        if 'SP' in filename:
                            os.rename(pasta_alvo+"/"+filename, pasta_alvo+"/"+filename.split('SP')[0]+UF+'.csv')
                        elif '_sp' in filename: 
                            os.rename(pasta_alvo+"/"+filename, pasta_alvo+"/"+filename.split('_sp')[0]+'_'+UF+'.csv')

        url = 'https://geoftp.ibge.gov.br/'
        conexao = ''
        try:
            response = requests.get(url, verify=False)
            conexao = True
        except requests.ConnectionError as exception:
            print (exception)
            conexao = False
            
        if conexao == True:
       
            progressMessageBar = self.iface.messageBar().createMessage("Baixando dados do Estado...")
            progress = QProgressBar()
            progress.setMaximum(5)
            progress.setAlignment(Qt.AlignLeft|Qt.AlignVCenter)
            progressMessageBar.layout().addWidget(progress)
            self.iface.messageBar().pushWidget(progressMessageBar, Qgis.Info)
            self.iface.messageBar().pushWidget(progressMessageBar, Qgis.Info)
            self.i = 0
            pasta = self.plugin_dir+'/dados_IBGE'
            baixa_setores(UF[:2], UF_codigo, pasta)
            baixa_dados(UF, pasta, estado)
            self.iface.messageBar().clearWidgets()
            #arruma_pastas(UF, pasta, estado)
        else:
            self.iface.messageBar().pushMessage("Não foi possível acessar a url:" +url, Qgis.Critical)         
        
    def popula_municipios(self, codigo_UF, estado):
        self.dlg.municipioComboBox.clear()
        if estado == 'SP_Capital':
            self.lista_municipios = {'São paulo':'3550308'}
        else:
            self.layer_municipios = QgsVectorLayer(self.plugin_dir+'/dados_IBGE/'+codigo_UF+'MUE250GC_SIR.shp', "municpios", "ogr")
            self.lista_municipios = {'':''}

            for municipio in self.layer_municipios.getFeatures():
                if municipio.attribute('NM_MUNICIP') != 'SÃO PAULO':
                    self.lista_municipios[municipio.attribute('NM_MUNICIP')] = municipio.attribute('CD_GEOCODM')
                
        self.dlg.municipioComboBox.addItems(self.lista_municipios.keys())

    def popula_dados(self, descr_tabela):
        self.dlg.listBox_disponiveis.clear()
        #tabela = self.dict_lista_tabela[self.dlg.tabelaComboBox.currentText()]   
        sum_list = []
        for item in self.tabela_dados.items():
            if item[1][0] == descr_tabela:
                for (item1, item2) in zip(item[1][1].keys(), item[1][1].values()):
                    sum_list.append(item1+': '+item2 +': '+ item[0])
                                
        self.dlg.listBox_disponiveis.addItems(sum_list)

    def movimenta_item(self, origem, destino, todos = False):
        if todos:
            origem.selectAll()
        items = origem.selectedItems()        
        for i in items:
            destino.addItem(i.text())
        model = origem.model()
        for selectedItem in origem.selectedItems():
            qIndex = origem.indexFromItem(selectedItem)
            model.removeRow(qIndex.row())    

    def abre_doc(self):
        path =  'file:///'+self.plugin_dir+u'/BASE DE INFORMACOES POR SETOR CENSITARIO Censo 2010 - Universo.pdf'
        webbrowser.open_new_tab(path)
 
    def abre_manual(self):
        path =  'file:///'+self.plugin_dir+u'/Manual.pdf'
        webbrowser.open_new_tab(path)
        
    def seleciona_categoriza(self):
        self.lista_categoriza = self.dlg.listBox_selecionados.selectedItems()
        texto = ''
        for x in self.lista_categoriza:
            texto =  texto + x.text()[:4] + ' + '
        self.dlg.textBrowser_soma.setText(texto[:-3])

    def seleciona_divide(self):
        self.lista_divide = self.dlg.listBox_selecionados.selectedItems()
        texto = ''
        for x in self.lista_divide:
            texto =  texto + x.text()[:4] + ' + '
        self.dlg.textBrowser_divi.setText(texto[:-3])    
      
    def uni_setor_atributos(self, QListWidget, estado, codigo_estado, municipio):
        dict_dados = {}
        lst = QListWidget
        items = []
        for x in range(lst.count()):
            items.append(lst.item(x).text())
            planilha = lst.item(x).text().split(':')[2][1:]
            coluna = lst.item(x).text().split(':')[0]        
            if planilha not in dict_dados.keys():
                dict_dados[planilha] = [coluna]
            else:
                dict_dados[planilha].append(coluna)
        
        layer_setores = QgsVectorLayer(self.plugin_dir+'/dados_IBGE/'+codigo_estado+'SEE250GC_SIR.shp', "setores", "ogr")
        #QgsProject.instance().addMapLayer(layer_setores)
        if municipio != '':
            # Extrair por atributo
            alg_params = {
                'FIELD': 'CD_GEOCODI',
                'INPUT': layer_setores,
                'OPERATOR': 6,
                'VALUE': municipio,
                'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
            }
            outputs= processing.run('native:extractbyattribute', alg_params)
            layer_setores = outputs['OUTPUT']
        print(dict_dados)
        #adiciona situacao e tipo
        if int(self.dlg.listBox_selecionados.count()) > 0:   
            if 'SP' not in estado:
                estado2 = estado     
            elif 'SP_Capital'  in estado:
                estado2 = 'SP1'
            elif 'SP_Exceto_Capital'  in estado:
                estado2 = 'SP2'
                 
            caminho_planilha = '{0}/dados_IBGE/Base informaçoes setores2010 universo {1}/CSV/{2}_{3}.csv'.format(self.plugin_dir, estado,  'Basico', estado2)
            print(caminho_planilha)
            layer_planilha = QgsVectorLayer(caminho_planilha, planilha, "ogr")
            #QgsProject.instance().addMapLayer(layer_planilha)
            alg_params = {
                'DISCARD_NONMATCHING': False,
                'FIELD': 'CD_GEOCODI',
                'FIELDS_TO_COPY': ['Situacao_setor','Tipo_setor'] ,
                'FIELD_2': 'Cod_setor',
                'INPUT': layer_setores,
                'INPUT_2': layer_planilha,
                'METHOD': 1,
                'PREFIX': '_',
                'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
            }
            outputs = processing.run('native:joinattributestable', alg_params)
            layer_setores = outputs['OUTPUT']        

            for planilha in dict_dados.keys():
                caminho_planilha = '{0}/dados_IBGE/Base informaçoes setores2010 universo {1}/CSV/{2}_{3}.csv'.format(self.plugin_dir, estado,  planilha, estado2)
                #ve se uf está minúscula
                caminho_planilha_mi = '{0}/dados_IBGE/Base informaçoes setores2010 universo {1}/CSV/{2}_{3}.csv'.format(self.plugin_dir, estado,  planilha, estado2.lower())
                if  os.path.isfile(caminho_planilha_mi):
                    caminho_planilha = caminho_planilha_mi
                print(caminho_planilha)    
                layer_planilha = QgsVectorLayer(caminho_planilha, planilha, "ogr")
                #QgsProject.instance().addMapLayer(layer_planilha)
                alg_params = {
                    'DISCARD_NONMATCHING': False,
                    'FIELD': 'CD_GEOCODI',
                    'FIELDS_TO_COPY': dict_dados[planilha],
                    'FIELD_2': 'Cod_setor',
                    'INPUT': layer_setores,
                    'INPUT_2': layer_planilha,
                    'METHOD': 1,
                    'PREFIX': planilha+'_',
                    'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
                }
                outputs = processing.run('native:joinattributestable', alg_params)
                layer_setores = outputs['OUTPUT']
            
                #setores_municipio = outputs['ExtrairPorAtributo']['OUTPUT']
            
        QgsProject.instance().addMapLayer(layer_setores)
        layer_setores.setName('Setores_censitários')
        layer_setores.loadNamedStyle(self.plugin_dir+'/estilos_camadas/setores.qml')  
        layer_setores.triggerRepaint()   
        if self.dlg.textBrowser_soma.toPlainText() != '':
            lista_cat = []
            items = self.lista_categoriza    
            nome = 'Categoria'
            for i in items:
                lista_cat.append(i.text().split(':')[2][1:]+'_'+i.text().split(':')[0])
                
            field = QgsField( nome, QVariant.Double )
            expr = ''
            for x in lista_cat:
                expr = expr+'to_real(replace("'+ x + """", ',', '.')) + """

            if self.dlg.textBrowser_divi.toPlainText() != '':
                items = self.lista_divide
                lista_div = []
                for i in items:
                    lista_div.append(i.text().split(':')[2][1:]+'_'+i.text().split(':')[0])
                expr = '('+ expr[:-3] + ')/('    
                for x in lista_div:
                    expr = expr+'to_real(replace("'+ x + """", ',', '.')) + """                
                expr = expr[:-3] + ')'
            else:
                 expr = expr[:-3]
            layer_setores.addExpressionField(expr, field )
            renderer = QgsGraduatedSymbolRenderer() 
            renderer.setClassAttribute('Categoria') 
            layer_setores.setRenderer(renderer) 
            layer_setores.renderer().updateClasses(layer_setores, QgsGraduatedSymbolRenderer.Quantile, 5)
            layer_setores.renderer().updateColorRamp(QgsGradientColorRamp(Qt.green, Qt.red)) 
            layer_setores.setOpacity(0.4)
            self.iface.layerTreeView().refreshLayerSymbology(layer_setores.id())
            self.iface.mapCanvas().refreshAllLayers()

    def carrega_demais_camadas(self, estado, codigo_estado, municipio):
        dict_camadas = {'DSE250GC_SIR.shp':['Distrito','CD_GEOCODD'],'MUE250GC_SIR.shp': ['Município', 'CD_GEOCODM'], 'SDE250GC_SIR.shp':['Subdistrito', 'CD_GEOCODS']} 
        for camada in dict_camadas.keys():
            layer = QgsVectorLayer(self.plugin_dir+'/dados_IBGE/'+codigo_estado+camada, dict_camadas[camada][0], "ogr")           
            if municipio != '':
                # Extrair por atributo
                alg_params = {
                    'FIELD': dict_camadas[camada][1],
                    'INPUT': layer,
                    'OPERATOR': 6,
                    'VALUE': municipio,
                    'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
                }
                outputs= processing.run('native:extractbyattribute', alg_params)
                layer = outputs['OUTPUT']
                
                
            QgsProject.instance().addMapLayer(layer)    
            layer.loadNamedStyle('{0}/estilos_camadas/{1}.qml'.format(self.plugin_dir, dict_camadas[camada][0]))  
            layer.triggerRepaint()  
            layer.setName(dict_camadas[camada][0])
            
    def run(self):
        """Run method that performs all the real work"""

        # Create the dialog with elements (after translation) and keep reference
        # Only create GUI ONCE in callback, so that it will only load when the plugin is started
        if self.first_start == True:
            self.first_start = False
            self.dlg = DadosCensoDialog()
            self.dlg.estadoComboBox.addItems(lista_estados.keys())
            path = os.path.join(
                    self.plugin_dir,
                    'tabelas_dados_censo_2010.txt')            
            file = open(path)
            contents = file.read()
            self.tabela_dados = ast.literal_eval(contents)
            lista_tabelas = []
            self.lista_selecionados = []
            #self.dict_lista_tabela = {}
            for key in self.tabela_dados.keys():
                value = self.tabela_dados[key][0]
                lista_tabelas.append(value)
                #self.dict_lista_tabela[value] = key
            lista_tabelas.insert(0, '')
            self.dlg.tabelaComboBox.addItems(lista_tabelas)
        
        # show the dialog
        self.limpa_dados()
        self.dlg.show()
        self.dlg.estadoComboBox.currentIndexChanged.connect(lambda: self.baixa_dados_estado(lista_estados[self.dlg.estadoComboBox.currentText()][0], lista_estados[self.dlg.estadoComboBox.currentText()][1], self.dlg.estadoComboBox.currentText())) 
        self.dlg.estadoComboBox.currentIndexChanged.connect(lambda: self.popula_municipios(lista_estados[self.dlg.estadoComboBox.currentText()][1], lista_estados[self.dlg.estadoComboBox.currentText()][0]))
        self.dlg.tabelaComboBox.currentIndexChanged.connect(lambda: self.popula_dados(self.dlg.tabelaComboBox.currentText()))
        self.dlg.pushButton_Seleciona.clicked.connect(lambda:self.movimenta_item(self.dlg.listBox_disponiveis, self.dlg.listBox_selecionados))
        self.dlg.pushButton_SelecionaTodos.clicked.connect(lambda:self.movimenta_item(self.dlg.listBox_disponiveis, self.dlg.listBox_selecionados, True))
        self.dlg.pushButton_Retira.clicked.connect(lambda:self.movimenta_item(self.dlg.listBox_selecionados, self.dlg.listBox_disponiveis))
        self.dlg.pushButton_RetiraTodos.clicked.connect(lambda:self.movimenta_item(self.dlg.listBox_selecionados, self.dlg.listBox_disponiveis, True)) 
        self.dlg.pushButton_categoriza.clicked.connect(lambda:self.seleciona_categoriza())  
        self.dlg.pushButton_divi.clicked.connect(lambda:self.seleciona_divide())
        self.dlg.pushButton_Doc.clicked.connect(lambda:self.abre_doc())
        self.dlg.pushButton_Manual.clicked.connect(lambda:self.abre_manual())



        # Run the dialog event loop
        result = self.dlg.exec_()
        # See if OK was pressed
        if result:
            # Do something useful here - delete the line containing pass and
            # substitute with your code.
            estado = lista_estados[self.dlg.estadoComboBox.currentText()][0]
            codigo_estado = lista_estados[self.dlg.estadoComboBox.currentText()][1]
            municipio =  self.lista_municipios[self.dlg.municipioComboBox.currentText()]
            self.uni_setor_atributos(self.dlg.listBox_selecionados, estado, codigo_estado, municipio)
            if self.dlg.checkBox_camadas.isChecked():
                self.carrega_demais_camadas(estado, codigo_estado[:2], municipio)                        

            
            pass
