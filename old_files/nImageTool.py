#from PyQt5 import QtWidgets, QtCore
from Macros_29id.PyImageTool.pyimagetool.ImageTool import ImageTool
from Macros_29id.PyImageTool.pyimagetool.DataMatrix import RegularDataArray

def nIT(d):
    """
    d=pynData object
    """
    axList=['x','y','z','t']
    axes=[]
    for ax in axList[0:len(d.data.shape)] :
        axes.insert(0, d.scale[ax])
    img=RegularDataArray(d.data,axes=tuple(axes))
    IT=ImageTool(img)
    IT.show()
    return IT


