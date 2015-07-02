# -*- coding: utf-8 -*-
##############################################################################
#    *************************************************************************
#    ********************* CODEGEN ODOO 2015 V1 ******************************
#    *************************************************************************
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
#    Este programa es software libre: usted puede redistribuirlo y / o modificarlo
#    bajo los t&eacute;rminos de la Licencia P&uacute;blica General Affero GNU como
#    publicada por la Free Software Foundation, bien de la versi&oacute;n 3 de la
#    Licencia, o (a su elecci&oacute;n) cualquier versi&oacute;n posterior.
#
#    Este programa se distribuye con la esperanza de que sea &uacute;til,
#    pero SIN NINGUNA GARANT&Iacute;A; ni siquiera la garant&iacute;a impl&iacute;cita de
#    COMERCIALIZACI&Oacute;N o IDONEIDAD PARA UN PROP&Oacute;SITO PARTICULAR. Vea el
#    GNU Affero General Public License para m&aacute;s detalles.
#
#    Deber&iacute;a haber recibido una copia de la Licencia P&uacute;blica General Affero GNU
#    junto con este programa. Si no es as&iacute;, consulte  <http://www.gnu.org/licenses/>.
#                                      
###############################################################################

import sys, dia, os
import zipfile

#
# This code is inspired by codegen.py
#
class Klass :
    def __init__ (self, name) :
        self.name = name
        self.attributes = []
        # a list, as java/c++ support multiple methods with the same name
        self.stereotype = ""
        self.operations = []
        self.comment = ""
        self.parents = []
        self.templates = []
        self.inheritance_type = ""
    def AddAttribute(self, name, type, visibility, value, comment) :
        self.attributes.append((name, (type, visibility, value, comment)))
    def AddOperation(self, name, type, visibility, params, inheritance_type, comment, class_scope) :
        self.operations.append((name,(type, visibility, params, inheritance_type, comment, class_scope)))
    def SetComment(self, s) :
        self.comment = s
    def AddParent(self, parent):
        self.parents.append(parent)
    def AddTemplate(self, template):
        self.templates.append(template)
    def SetInheritance_type(self, inheritance_type):
        self.inheritance_type = inheritance_type

class ObjRenderer :
    "Implementa la interfaz Renderer Objeto y transforma diagrama en su representación interna"
    def __init__ (self) :
        # un diccionario vacío de clases
        self.klasses = {}
        self.klass_names = []   # nombres de clases tienda para mantener el orden
        self.arrows = []
        self.filename = ""
        
    def begin_render (self, data, filename) :
        self.filename = filename
        for layer in data.layers :
            # por el momento ignorar info capa. Pero podríamos usar esto para difundir a través de diferentes archivos
            for o in layer.objects :
                if o.type.name == "UML - Class" :

                    k = Klass (o.properties["name"].value)
                    k.SetComment(o.properties["comment"].value)
                    k.stereotype = o.properties["stereotype"].value
                    if o.properties["abstract"].value:
                        k.SetInheritance_type("abstract")
                    if o.properties["template"].value:
                        k.SetInheritance_type("template")
                    for op in o.properties["operations"].value :
                        # op : a tuple with fixed placing, see: objects/UML/umloperations.c:umloperation_props
                        # (name, type, comment, stereotype, visibility, inheritance_type, class_scope, params)
                        params = []
                        for par in op[8] :
                            # par : again fixed placement, see objects/UML/umlparameter.c:umlparameter_props
                            params.append((par[0], par[1]))
                        k.AddOperation (op[0], op[1], op[4], params, op[5], op[2], op[7])
                    #print o.properties["attributes"].value
                    for attr in o.properties["attributes"].value :
                        # see objects/UML/umlattributes.c:umlattribute_props
                        #print "    ", attr[0], attr[1], attr[4]
                        k.AddAttribute(attr[0], attr[1], attr[4], attr[2], attr[3])
                    self.klasses[o.properties["name"].value] = k
                    self.klass_names += [o.properties["name"].value]
                    #Connections
                elif o.type.name == "UML - Association" :
                    # should already have got attributes relation by names
                    pass
                # other UML objects which may be interesting
                # UML - Note, UML - LargePackage, UML - SmallPackage, UML - Dependency, ...
        
        edges = {}
        for layer in data.layers :
            for o in layer.objects :
                for c in o.connections:
                    for n in c.connected:
                        if not n.type.name in ("UML - Generalization", "UML - Realizes"):
                            continue
                        if str(n) in edges:
                            continue
                        edges[str(n)] = None
                        if not (n.handles[0].connected_to and n.handles[1].connected_to):
                            continue
                        par = n.handles[0].connected_to.object
                        chi = n.handles[1].connected_to.object
                        if not par.type.name == "UML - Class" and chi.type.name == "UML - Class":
                            continue
                        par_name = par.properties["name"].value
                        chi_name = chi.properties["name"].value
                        if n.type.name == "UML - Generalization":
                            self.klasses[chi_name].AddParent(par_name)
                        else: self.klasses[chi_name].AddTemplate(par_name)
                    
    def end_render(self) :
        # without this we would accumulate info from every pass
        self.attributes = []
        self.operations = {}


class OpenERPRenderer(ObjRenderer) : 
    def __init__(self) :
        ObjRenderer.__init__(self)

    def data_get(self):
        return {
            'file': self.filename,
            'module': os.path.basename(self.filename).split('.')[-2]
        }

    def terp_get(self):
        terp = """# -*- coding: utf-8 -*-
##############################################################################
#    *************************************************************************
#    ********************* CODEGEN ODOO 2015 V1 ******************************
#    *************************************************************************
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
#    Este programa es software libre: usted puede redistribuirlo y / o modificarlo
#    bajo los t&eacute;rminos de la Licencia P&uacute;blica General Affero GNU como
#    publicada por la Free Software Foundation, bien de la versi&oacute;n 3 de la
#    Licencia, o (a su elecci&oacute;n) cualquier versi&oacute;n posterior.
#
#    Este programa se distribuye con la esperanza de que sea &uacute;til,
#    pero SIN NINGUNA GARANT&Iacute;A; ni siquiera la garant&iacute;a impl&iacute;cita de
#    COMERCIALIZACI&Oacute;N o IDONEIDAD PARA UN PROP&Oacute;SITO PARTICULAR. Vea el
#    GNU Affero General Public License para m&aacute;s detalles.
#
#    Deber&iacute;a haber recibido una copia de la Licencia P&uacute;blica General Affero GNU
#    junto con este programa. Si no es as&iacute;, consulte  <http://www.gnu.org/licenses/>.
#                                      
###############################################################################
# Generated by the OpenERP plugin for Dia !
{
        "name" : "%(module)s",
        "version" : "0.2",
        "author" : "Mario Sandoval",
        "website" : "https://twitter.com/MarioSandovalP3",
        "category" : "Desconocido",
        "summary": "",
        "description": \"\"\"  \"\"\",
        "depends" : ['base'],
        "init_xml" : [ ],
        "demo_xml" : [ ],
        "update_xml" : ['vistas/%(module)s_view.xml', 'security/ir.model.access.csv'],
        "installable": True
}""" % self.data_get()
        return terp

    def init_get(self):
        return """# -*- coding: utf-8 -*-
##############################################################################
#    *************************************************************************
#    ********************* CODEGEN ODOO 2015 V1 ******************************
#    *************************************************************************
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
#    Este programa es software libre: usted puede redistribuirlo y / o modificarlo
#    bajo los t&eacute;rminos de la Licencia P&uacute;blica General Affero GNU como
#    publicada por la Free Software Foundation, bien de la versi&oacute;n 3 de la
#    Licencia, o (a su elecci&oacute;n) cualquier versi&oacute;n posterior.
#
#    Este programa se distribuye con la esperanza de que sea &uacute;til,
#    pero SIN NINGUNA GARANT&Iacute;A; ni siquiera la garant&iacute;a impl&iacute;cita de
#    COMERCIALIZACI&Oacute;N o IDONEIDAD PARA UN PROP&Oacute;SITO PARTICULAR. Vea el
#    GNU Affero General Public License para m&aacute;s detalles.
#
#    Deber&iacute;a haber recibido una copia de la Licencia P&uacute;blica General Affero GNU
#    junto con este programa. Si no es as&iacute;, consulte  <http://www.gnu.org/licenses/>.
#                                      
###############################################################################
# Generated by the OpenERP plugin for Dia !\n#\n\nimport modelos.%(module)s""" % self.data_get()


    def init_model_get(self):
        return """# -*- coding: utf-8 -*-
##############################################################################
#    *************************************************************************
#    ********************* CODEGEN ODOO 2015 V1 ******************************
#    *************************************************************************
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
#    Este programa es software libre: usted puede redistribuirlo y / o modificarlo
#    bajo los t&eacute;rminos de la Licencia P&uacute;blica General Affero GNU como
#    publicada por la Free Software Foundation, bien de la versi&oacute;n 3 de la
#    Licencia, o (a su elecci&oacute;n) cualquier versi&oacute;n posterior.
#
#    Este programa se distribuye con la esperanza de que sea &uacute;til,
#    pero SIN NINGUNA GARANT&Iacute;A; ni siquiera la garant&iacute;a impl&iacute;cita de
#    COMERCIALIZACI&Oacute;N o IDONEIDAD PARA UN PROP&Oacute;SITO PARTICULAR. Vea el
#    GNU Affero General Public License para m&aacute;s detalles.
#
#    Deber&iacute;a haber recibido una copia de la Licencia P&uacute;blica General Affero GNU
#    junto con este programa. Si no es as&iacute;, consulte  <http://www.gnu.org/licenses/>.
#                                      
###############################################################################
# Generated by the OpenERP plugin for Dia !\n#\n\nimport %(module)s""" % self.data_get()
    
    def security_get(self):
        header = """"id","name","model_id:id","group_id:id","perm_read","perm_write","perm_create","perm_unlink"\n"""
        
        rows = """"access_%s","%s","model_%s","base.group_user",1,0,1,0"""
        for clas in self.klass_names:
            cname = clas.replace('.', '_')
            header += rows % (cname, clas, cname) + '\n'
        return header


    def get_label(self, attrs):
        label = None
        if attrs[0] == 'many2many':
            for att in attrs[2].split(','):
                if 'string' in att:
                    label = att[8:]
            if not label:
                label = attrs[2].split(',')[4]
        if attrs[0] == 'one2many':
            for att in attrs[2].split(','):
                if 'string' in att:
                    label = att[8:]
            if not label:
                label = attrs[2].split(',')[2]
        if attrs[0] == 'text':
            for att in attrs[2].split(','):
                if 'string' in att:
                    label = att[8:]
            if not label:
                label = attrs[2].split(',')[0]
        return label

    def view_class_get(self, cn, cd):
        data = self.data_get()
        i = 1
        fields_form = fields_tree = ""
        cols = {}
        for sa,attr in cd.attributes:
            cols[sa] = True
            attrs = ''
            if attr[0] in ('one2many', 'many2many', 'text'):
                attrs='colspan="4" nolabel="1" '
                field_label = self.get_label(attr)
                fields_form += ("                <separator string=\"%s\" colspan=\"4\"/>\n") % (field_label or 'Unknown')
            fields_form += ("                <field name=\"%s\" "+attrs+"select=\"%d\"/>\n") % (sa,i)
            if attr[0] not in ('one2many', 'many2many'):
                fields_tree += "                <field name=\"%s\"/>\n" % (sa,)
            if (i==2) or not i:
                i=-1
            i += 1
        data['form']= fields_form
        data['tree']= fields_tree
        data['name_id']= cn.replace('.','_')
        if not cd.stereotype:
            data['menu']= 'Unknown/'+cn.replace('.','_')
        else:
            data['menu']= cd.stereotype
            data['comentario']= cd.comment
        data['name']= cn
        data['name_en']= data['menu'].split('/')[-1]
        data['mode'] = 'tree,form'
        if 'date' in cols:
            data['mode']='tree,form,calendar'
        result = """
    <record model="ir.ui.view" id="view_%(name_id)s_form">
        <field name="name">%(name)s.form</field>
        <field name="model">%(name)s</field>
        <field name="type">form</field>
        <field name="arch" type="xml">
            <form string="%(name)s">
                <sheet>
                   <notebook colspan="4">
                     <page string="%(name_en)s">
                       <group col="4" colspan="4">
%(form)s
                       </group>
                               
                     </page>
                  </notebook>
                </sheet>
            </form>
        </field>
    </record>
    <record model="ir.ui.view" id="view_%(name_id)s_tree">
        <field name="name">%(name)s.tree</field>
        <field name="model">%(name)s</field>
        <field name="type">tree</field>
        <field name="arch" type="xml">
            <tree string="%(name)s">
%(tree)s
            </tree>
        </field>
    </record>
    <record model="ir.actions.act_window" id="action_%(name_id)s">
        <field name="name">%(name_en)s</field>
        <field name="res_model">%(name)s</field>
        <field name="view_type">form</field>
        <field name="view_mode">%(mode)s</field>
        <field name="help" type="html">
                <p class="oe_view_nocontent_create">
                    Haz click aquí
                </p><p>
                    <h3>%(comentario)s</h3>
                </p>
        </field>
    </record>
 <menuitem name="%(menu)s" id="menu_%(name_id)s" action="action_%(name_id)s"/>
        """ % data
        return result

    def view_get(self):
        result = """<?xml version="1.0" encoding="UTF-8"?>
<openerp>
<data>
"""
        for sk in self.klass_names:
            result += self.view_class_get(sk, self.klasses[sk])
        result += """
</data>
</openerp>"""
        return result

    def code_get(self):
        result = """# -*- coding: utf-8 -*-
##############################################################################
#    *************************************************************************
#    ********************* CODEGEN ODOO 2015 V1 ******************************
#    *************************************************************************
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
#    Este programa es software libre: usted puede redistribuirlo y / o modificarlo
#    bajo los t&eacute;rminos de la Licencia P&uacute;blica General Affero GNU como
#    publicada por la Free Software Foundation, bien de la versi&oacute;n 3 de la
#    Licencia, o (a su elecci&oacute;n) cualquier versi&oacute;n posterior.
#
#    Este programa se distribuye con la esperanza de que sea &uacute;til,
#    pero SIN NINGUNA GARANT&Iacute;A; ni siquiera la garant&iacute;a impl&iacute;cita de
#    COMERCIALIZACI&Oacute;N o IDONEIDAD PARA UN PROP&Oacute;SITO PARTICULAR. Vea el
#    GNU Affero General Public License para m&aacute;s detalles.
#
#    Deber&iacute;a haber recibido una copia de la Licencia P&uacute;blica General Affero GNU
#    junto con este programa. Si no es as&iacute;, consulte  <http://www.gnu.org/licenses/>.
#                                      
###############################################################################
# Generated by the OpenERP plugin for Dia !
from openerp.osv import fields,osv
"""     
        for sk in self.klass_names:
            cname = sk.replace('.','_')
            result += "class %s(osv.osv):\n" % (cname,)
            if self.klasses[sk].comment:
                result += "    "+'"""'+self.klasses[sk].comment+'"""\n'
            result += "    _name = '%s'\n" % (sk,)


            parents = self.klasses[sk].parents
            if parents:
                result += "    _inherit = '"+parents[0]+"'\n"
            templates = self.klasses[sk].templates
            if templates:
                result += "    _inherits = {'"+templates[0]+"':'"+templates[0]+"'}\n"


            default = {}
            result += "    _columns = {\n"
            for sa,attr in self.klasses[sk].attributes :
                value = attr[2]
                if attr[3]:
                    value += ", help='%s'" % (attr[3].replace("'"," "),)
                attr_type = attr[0]
                result += "        '%s': fields.%s(%s),\n" % (sa, attr_type, value)
            result += "    }\n"

            if default:
                result += '    _defaults = {'
                for d in default:
                    result += "        '%s':lambda *args: '%s'\n" % (d, default[d])
                result += '    }'

            for so, op in self.klasses[sk].operations :
                pars = "self, cr, uid, ids"
                for p in op[2] :
                    pars = pars + ", " + p[0]
                result+="    def %s(%s) :\n" % (so, pars)
                if op[4]: result+="        \"\"\" %s \"\"\"\n" % op[4]
                result+="        # returns %s\n" % (op[0], )
            result += cname+"()\n\n"
        return result
    
    def html_get(self):
        html = """<!doctype html>
<html>
<head>
<meta charset="utf-8">
<title>Codegen OdooERP</title>
<style>
	
	
	body {
		
		font:14px/1.5 Arial, sans-serif;
		text-align:center;
		color:#333;
		background:#fff;
	}

	a {
		font-weight:bold;
		color:#dd3333;
		
	}

	a:hover,
	a:focus,
	a:active {
		text-decoration:none;
	}
	h1{
	font-size:58px
	}

	.container {
		position:relative;
		z-index:1;
		width:900px;
		
		margin:0 auto;
		background:#fff;
	}

	.container:after {
		content:"";
		display:block;
		clear:both;
		visibility:hidden;
		height:0;
		font-size:0;
	}

	/* Sombra general */

	.drop-shadow {
		position:relative;
		
		width:80%;
		padding:1em;
		margin:2em 50px 4em;
		background:#fff;
		-webkit-box-shadow:0 1px 4px rgba(0, 0, 0, 0.3), 0 0 40px rgba(0, 0, 0, 0.1) inset;
		   -moz-box-shadow:0 1px 4px rgba(0, 0, 0, 0.3), 0 0 40px rgba(0, 0, 0, 0.1) inset;
				box-shadow:0 1px 4px rgba(0, 0, 0, 0.3), 0 0 40px rgba(0, 0, 0, 0.1) inset;
	}

	.drop-shadow:before,
	.drop-shadow:after {
		content:"";
		position:absolute;
		z-index:-2;
	}

	.drop-shadow p {
		font-size:16px;
		font-weight:bold;
	}

	/* Bordes redondeados */

	.lifted {
		-moz-border-radius:4px;
			 border-radius:4px;
	}

	.lifted:before,
	.lifted:after {
		bottom:15px;
		left:10px;
		width:50%;
		height:20%;
		max-width:300px;
		max-height:100px;
		-webkit-box-shadow:0 15px 10px rgba(0, 0, 0, 0.7);
		   -moz-box-shadow:0 15px 10px rgba(0, 0, 0, 0.7);
				box-shadow:0 15px 10px rgba(0, 0, 0, 0.7);
		-webkit-transform:rotate(-3deg);
		   -moz-transform:rotate(-3deg);
			-ms-transform:rotate(-3deg);
			 -o-transform:rotate(-3deg);
				transform:rotate(-3deg);
	}

	.lifted:after {
		right:10px;
		left:auto;
		-webkit-transform:rotate(3deg);
		   -moz-transform:rotate(3deg);
			-ms-transform:rotate(3deg);
			 -o-transform:rotate(3deg);
				transform:rotate(3deg);
	}


	.rotated {
		-webkit-box-shadow:none;
		   -moz-box-shadow:none;
				box-shadow:none;
		-webkit-transform:rotate(-3deg);
		   -moz-transform:rotate(-3deg);
			-ms-transform:rotate(-3deg);
			 -o-transform:rotate(-3deg);
				transform:rotate(-3deg);
	}

	.rotated > :first-child:before {
		content:"";
		position:absolute;
		z-index:-1;
		top:0;
		bottom:0;
		left:0;
		right:0;
		background:#fff;
		-webkit-box-shadow:0 1px 4px rgba(0, 0, 0, 0.3), 0 0 40px rgba(0, 0, 0, 0.1) inset;
		   -moz-box-shadow:0 1px 4px rgba(0, 0, 0, 0.3), 0 0 40px rgba(0, 0, 0, 0.1) inset;
				box-shadow:0 1px 4px rgba(0, 0, 0, 0.3), 0 0 40px rgba(0, 0, 0, 0.1) inset;
	}

</style>
</head>

<body>
<div class="container">
        <h1><a href="https://github.com/MarioSandoval/Odoo/">Codegen Odoo ERP</a></h1>

        

        <div class="drop-shadow lifted rotated" align="left">
            <pre>
##########################################################################################
#    *************************************************************************************
#    ********************* CODEGEN ODOO 2015 V1 ******************************************
#    *************************************************************************************
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
#    Este programa es software libre: usted puede redistribuirlo y / o modificarlo
#    bajo los t&eacute;rminos de la Licencia P&uacute;blica General Affero GNU como
#    publicada por la Free Software Foundation, bien de la versi&oacute;n 3 de la
#    Licencia, o (a su elecci&oacute;n) cualquier versi&oacute;n posterior.
#
#    Este programa se distribuye con la esperanza de que sea &uacute;til,
#    pero SIN NINGUNA GARANT&Iacute;A; ni siquiera la garant&iacute;a impl&iacute;cita de
#    COMERCIALIZACI&Oacute;N o IDONEIDAD PARA UN PROP&Oacute;SITO PARTICULAR. Vea el
#    GNU Affero General Public License para m&aacute;s detalles.
#
#    Deber&iacute;a haber recibido una copia de la Licencia P&uacute;blica General Affero GNU
#    junto con este programa. Si no es as&iacute;, consulte  <a href="http://www.gnu.org/licenses/" target="_BLANK">http://www.gnu.org/licenses/</a>.
#                                      
###########################################################################################
</pre>
        </div>
    </div>
</body>
</html>
""" 
        return html

 
  

    def end_render(self) :
        module = self.data_get()['module']
        zip = zipfile.ZipFile(self.filename, 'w')
        filewrite = {
                'leer.html':self.html_get(),
                '__init__.py':self.init_get(),
                '__openerp__.py':self.terp_get(),
                'modelos/'+module+'.py': self.code_get(),
                'modelos/__init__.py': self.init_model_get(),
                'vistas/'+module+'_view.xml': self.view_get(),
                'static/description/': self.view_get(),
                'security/ir.model.access.csv': self.security_get()
        }
        for name,datastr in filewrite.items():
            info = zipfile.ZipInfo(module+'/'+name)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 2175008768
            zip.writestr(info, datastr)
        zip.close()
        ObjRenderer.end_render(self)


# dia-python keeps a reference to the renderer class and uses it on demand
dia.register_export ("PyDia Code Generation (OpenERP)", "zip", OpenERPRenderer())

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
