# -*- coding: cp1251 -*-
import xml.dom.minidom
import sys
res=""

def parse_node(node,indent):
    global res
    if node.nodeType == xml.dom.Node.ELEMENT_NODE:
         res += (indent+node.nodeName+'\n')
         attribs=node.attributes
         for key in attribs.keys():
             res += (indent+key+"="+attribs[key].value+'\n')
         indent+=' '
    for c_node in node.childNodes:
         if c_node.nodeType == xml.dom.Node.ELEMENT_NODE and (len(c_node.childNodes)>0 or len(c_node.attributes.keys())>0):
             parse_node(c_node,indent)
         else:
             if c_node.nodeType == xml.dom.Node.ELEMENT_NODE:
                 res += (indent+c_node.nodeName+'\n')
    return 


def XmlToIni(infile):
  global res
  indent=""
  doc= xml.dom.minidom.parse(infile)
  res=""
  parse_node(doc,indent)
  return res

