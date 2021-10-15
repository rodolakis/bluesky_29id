import matplotlib.image as mpimg
import matplotlib.pyplot as plt



#  filepath='/home/beams/29IDUSER/Documents/User_Folders/Topp/S089.tif'
def plot_image(filepath,h=20,v=10):
    """
    filepath = '/home/beams/29IDUSER/Documents/User_Folders/UserName/TifFile.tif'
    """
    image = mpimg.imread(filepath)
    plt.figure(figsize=(h,v))
    #plt.imshow(image,cmap='gray',vmin=v1,vmax=v2)
    plt.imshow(image,cmap='gray')
    plt.axis('off')
    plt.show()
