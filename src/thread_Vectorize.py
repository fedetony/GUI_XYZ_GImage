'''
Code originally from Javier Rodriguez Second function
https://github.com/IngJavierR/PngToSvg.git
Latest commit a46b860 on May 7 
'''
from PIL import Image
import operator
from collections import deque
from io import StringIO
import threading

#import numba  # for GPU compile and usage
 
class Vectorization(threading.Thread):
    """
        A thread class Get vector data out of pillow and images in rgba form
    """
    def __init__(self, The_Image, kill_event,plaintextEdit_GcodeScript=None,Pbar=None):
        threading.Thread.__init__(self, name="Vectorize thread")        
        self.killer_event = kill_event
        self.im=The_Image
        self.improcess_percentage=0
        self.printprocess=False
        self.plaintextEdit_GcodeScript=plaintextEdit_GcodeScript
        self.Pbarupdate=Pbar
        self.Pbar_Set_Status(0)
        self.Pbarini=0
        self.Pbarend=100

    def Pbar_Set_Status(self,val):
        if  self.Pbarupdate!=None and int(val)>=0 and int(val)<=100:      
            self.Pbarupdate.SetStatus(int(val))    

    def Get_Im_Process_state(self):
        return self.improcess_percentage

    def add_tuple(self,a, b):
        return tuple(map(operator.add, a, b))

    def sub_tuple(self,a, b):
        return tuple(map(operator.sub, a, b))

    def neg_tuple(self,a):
        return tuple(map(operator.neg, a))

    def direction(self,edge):
        return self.sub_tuple(edge[1], edge[0])

    def magnitude(self,a):
        return int(pow(pow(a[0], 2) + pow(a[1], 2), .5))

    def normalize(self,a):
        mag = self.magnitude(a)
        assert mag > 0, "Cannot normalize a zero-length vector"
        return tuple(map(operator.truediv, a, [mag]*len(a)))

    def svg_header(self,width, height):
        return """<?xml version="1.0" encoding="UTF-8" standalone="no"?>
        <!DOCTYPE svg PUBLIC "-//W3C//DTD SVG 1.1//EN" 
        "http://www.w3.org/Graphics/SVG/1.1/DTD/svg11.dtd">
        <svg width="%d" height="%d"
            xmlns="http://www.w3.org/2000/svg" version="1.1">
        """ % (width, height)    
    #@numba.jit
    def joined_edges(self,assorted_edges, keep_every_point=False):
        pieces = []
        piece = []
        directions = deque([
            (0, 1),
            (1, 0),
            (0, -1),
            (-1, 0),
            ])
        while assorted_edges:
            if self.killer_event.is_set():
                break
            if not piece:
                piece.append(assorted_edges.pop())
            current_direction = self.normalize(self.direction(piece[-1]))
            while current_direction != directions[2]:
                directions.rotate()
            for i in range(1, 4):
                next_end = self.add_tuple(piece[-1][1], directions[i])
                next_edge = (piece[-1][1], next_end)
                if next_edge in assorted_edges:
                    assorted_edges.remove(next_edge)
                    if i == 2 and not keep_every_point:
                        # same direction
                        piece[-1] = (piece[-1][0], next_edge[1])
                    else:
                        piece.append(next_edge)
                    if piece[0][0] == piece[-1][1]:
                        if not keep_every_point and self.normalize(self.direction(piece[0])) == self.normalize(self.direction(piece[-1])):
                            piece[-1] = (piece[-1][0], piece.pop(0)[1])
                            # same direction
                        pieces.append(piece)
                        piece = []
                    break
            else:
                raise Exception ("Failed to find connecting edge")
        return pieces
    
    def rgba_image_to_svg_contiguous(self,im, opaque=None, keep_every_point=False):
        # collect contiguous pixel groups
        self.Pbarini=0
        self.Pbarend=25
        color_pixel_lists=self.collect_contiguous_pixel_groups(im, opaque, keep_every_point)
        # calculate clockwise edges of pixel groups
        self.Pbarini=25
        self.Pbarend=50
        color_edge_lists=self.calculate_clockwise_edges_of_pixel_groups(color_pixel_lists,opaque, keep_every_point)        
        # join edges of pixel groups
        self.Pbarini=50
        self.Pbarend=75
        color_joined_pieces=self.join_edges_of_pixel_groups(color_edge_lists,opaque, keep_every_point)                
        # Write svg format
        self.Pbarini=75
        self.Pbarend=100        
        svg= self.write_color_joined_pieces_to_svg_contiguous(im,color_joined_pieces)
        self.Pbarini=0
        self.Pbarend=100
        if self.printprocess==True:
            print('Amount of color layers processed:',len(color_joined_pieces))
        return svg
    
    #@numba.jit
    def collect_contiguous_pixel_groups(self,im, opaque=None, keep_every_point=False):
        # collect contiguous pixel groups        
        adjacent = ((1, 0), (0, 1), (-1, 0), (0, -1))
        visited = Image.new("1", im.size, 0)        
        color_pixel_lists = {}
        width, height = im.size
        
        self.improcess_percentage=self.Set_Progress_Percentage(0,width,self.Pbarini,self.Pbarend)
        for x in range(width):
            self.improcess_percentage=self.Set_Progress_Percentage(x,width,self.Pbarini,self.Pbarend)
            if self.killer_event.is_set():
                break
            for y in range(height):
                here = (x, y)
                if visited.getpixel(here):
                    continue
                rgba = im.getpixel((x, y))
                if opaque and not rgba[3]:
                    continue
                piece = []
                queue = [here]
                visited.putpixel(here, 1)
                while queue:
                    here = queue.pop()
                    for offset in adjacent:
                        neighbour = self.add_tuple(here, offset)
                        if not (0 <= neighbour[0] < width) or not (0 <= neighbour[1] < height):
                            continue
                        if visited.getpixel(neighbour):
                            continue
                        neighbour_rgba = im.getpixel(neighbour)
                        if neighbour_rgba != rgba:
                            continue
                        queue.append(neighbour)
                        visited.putpixel(neighbour, 1)
                    piece.append(here)

                if not rgba in color_pixel_lists:
                    color_pixel_lists[rgba] = []
                color_pixel_lists[rgba].append(piece)

        #del adjacent
        #del visited
        return color_pixel_lists
    
    #@numba.jit
    def calculate_clockwise_edges_of_pixel_groups(self,color_pixel_lists, opaque=None, keep_every_point=False):
        edges = {
            (-1, 0):((0, 0), (0, 1)),
            (0, 1):((0, 1), (1, 1)),
            (1, 0):((1, 1), (1, 0)),
            (0, -1):((1, 0), (0, 0)),
            }                
        color_edge_lists = {}        
        lenlist=len(color_pixel_lists.items())
        sss=0
        for rgba, pieces in color_pixel_lists.items():
            self.improcess_percentage=self.Set_Progress_Percentage(sss,lenlist,self.Pbarini,self.Pbarend)
            if self.killer_event.is_set():
                break
            sss=sss+1
            for piece_pixel_list in pieces:
                edge_set = set([])
                for coord in piece_pixel_list:
                    for offset, (start_offset, end_offset) in edges.items():
                        neighbour = self.add_tuple(coord, offset)                        
                        if neighbour in piece_pixel_list:
                            continue
                        self.improcess_percentage=self.Set_Progress_Percentage(sss,lenlist,self.Pbarini,self.Pbarend)
                        start = self.add_tuple(coord, start_offset)
                        end = self.add_tuple(coord, end_offset)
                        edge = (start, end)
                        edge_set.add(edge)
                if not rgba in color_edge_lists:
                    color_edge_lists[rgba] = []
                color_edge_lists[rgba].append(edge_set)

        #del color_pixel_lists
        #del edges

        return color_edge_lists
    
    #@numba.jit
    def join_edges_of_pixel_groups(self,color_edge_lists,opaque=None, keep_every_point=False):
        color_joined_pieces = {}
        lenlist=len(color_edge_lists.items())
        sss=0
        for color, pieces in color_edge_lists.items():
            if self.killer_event.is_set():
                break
            self.improcess_percentage=self.Set_Progress_Percentage(sss,lenlist,self.Pbarini,self.Pbarend)
            sss=sss+1
            color_joined_pieces[color] = []
            for assorted_edges in pieces:
                color_joined_pieces[color].append(self.joined_edges(assorted_edges, keep_every_point))
        return color_joined_pieces

    def write_color_joined_pieces_to_svg_contiguous(self,im,color_joined_pieces):
        s = StringIO()
        s.write(self.svg_header(*im.size))

        lenlist=len(color_joined_pieces.items())
        sss=0
        for color, shapes in color_joined_pieces.items():
            if self.killer_event.is_set():
                break
            self.improcess_percentage=self.Set_Progress_Percentage(sss,lenlist,self.Pbarini,self.Pbarend)
            sss=sss+1
            for shape in shapes:
                s.write(""" <path d=" """)
                for sub_shape in shape:
                    here = sub_shape.pop(0)[0]
                    s.write(""" M %d,%d """ % here)
                    for edge in sub_shape:
                        here = edge[0]
                        s.write(""" L %d,%d """ % here)
                    s.write(""" Z """)
                s.write(""" " style="fill:rgb%s; fill-opacity:%.3f; stroke:none;" />\n""" % (color[0:3], float(color[3]) / 255))
                
        s.write("""</svg>\n""")
        return s.getvalue()    

    def Transform_pixel_coord_to_image_coord(self,im,x,y,Img_ini_pos,Robot_XYZ,Resolution=1):
        # (0,0) is the upper left corner
        y=im.height-y
        x=Resolution*x
        y=Resolution*y
        # Add robot image origin position
        y=y+Img_ini_pos[1]+Robot_XYZ[1]
        x=x+Img_ini_pos[0]+Robot_XYZ[0]
        return [x,y]
           
    def Get_color_joined_pieces_from_rgba_image(self,im, opaque=None, keep_every_point=False):
        color_joined_pieces={}
        # collect contiguous pixel groups
        self.Pbarini=0
        self.Pbarend=25
        color_pixel_lists=self.collect_contiguous_pixel_groups(im, opaque, keep_every_point)
        # calculate clockwise edges of pixel groups
        self.Pbarini=25
        self.Pbarend=75
        color_edge_lists=self.calculate_clockwise_edges_of_pixel_groups(color_pixel_lists,opaque, keep_every_point)        
        # join edges of pixel groups
        self.Pbarini=75
        self.Pbarend=100
        color_joined_pieces=self.join_edges_of_pixel_groups(color_edge_lists,opaque, keep_every_point)     
        self.Pbarini=0
        self.Pbarend=100   
        return color_joined_pieces  

    def rgba_image_to_svg_pixels(self,im, opaque=None):
        s = StringIO()
        s.write(self.svg_header(*im.size))

        width, height = im.size
        for x in range(width):
            for y in range(height):
                here = (x, y)
                rgba = im.getpixel(here)
                if opaque and not rgba[3]:
                    continue
                s.write("""  <rect x="%d" y="%d" width="1" height="1" style="fill:rgb%s; fill-opacity:%.3f; stroke:none;" />\n""" % (x, y, rgba[0:3], float(rgba[2]) / 255))
        s.write("""</svg>\n""")
        return s.getvalue()

    def Set_Progress_Percentage(self,sss,Numsss,Perini=0,Perend=100):
        if sss>Numsss:
            self.Pbar_Set_Status(Perend)
            return Perend
        if sss<0 or Numsss<=0:
            self.Pbar_Set_Status(Perini)
            return Perini
        if (Perend-Perini)<=0:
            Per=min(abs(Perini),abs(Perend))  
            self.Pbar_Set_Status(Per)
            return Per 
        Per=round(Perini+(sss/Numsss)*(Perend-Perini),2)
        if self.printprocess==True:
            print('Image Processed '+str(Per)+'%')
        self.Pbar_Set_Status(Per)
        return Per   

    def Vectorized_color_joined_pieces_to_gcode_contiguous(self,im,color_joined_pieces,Gimageinfo,TouchONgcode,TouchOFFgcode,addon='\n'):
        [Img_ini_pos,Robot_XYZ,Resolution,Feedrate]=Gimageinfo
        s = StringIO()
        #s.write(self.svg_header(*im.size))       
        lenlist=len(color_joined_pieces.items())
        sss=0
        for color, shapes in color_joined_pieces.items():
            if self.killer_event.is_set():
                break
            self.improcess_percentage=self.Set_Progress_Percentage(sss,lenlist,self.Pbarini,self.Pbarend)
            sss=sss+1
            for shape in shapes:  
                s.write(TouchOFFgcode)
                s.write(""" G1""")
                for sub_shape in shape:
                    here = sub_shape.pop(0)[0]
                    (x, y)=here
                    [x,y]=self.Transform_pixel_coord_to_image_coord(im,x,y,Img_ini_pos,Robot_XYZ,Resolution)
                    here=(x, y)
                    s.write(""" X%.3f Y%.3f""" % here)
                    s.write(""" F%.3f""" % Feedrate)
                    s.write("""%s""" % addon)
                    s.write(TouchONgcode)
                    for edge in sub_shape:
                        here = edge[0]
                        (x, y)=here
                        [x,y]=self.Transform_pixel_coord_to_image_coord(im,x,y,Img_ini_pos,Robot_XYZ,Resolution)
                        here=(x, y)
                        s.write("""G1 X%.3f Y%.3f""" % here)
                        s.write(""" F%d""" % Feedrate)
                        s.write("""%s""" % addon)
                    s.write(TouchOFFgcode)
                #s.write(""" " style="fill:rgb%s; fill-opacity:%.3f; stroke:none;" />\n""" % (color[0:3], float(color[3]) / 255))
                
        #s.write("""</svg>\n""")
        if self.printprocess==True:
            print('Amount of color layers processed:',lenlist)
        return s.getvalue()      
    
    def Sort_color_joined_pieces_by_color(self,color_joined_pieces):
        #Structure oreder is:
        #shapes=color_joined_pieces[color] # dictionary of colors
        #shape=shapes[0]
        #xylinesegments=shape[0]
        #one_xylinesegment=xylinesegments[0] #tuple of two (x,y) points making a line
        #xytuple=one_xylinesegment[0] #tuple of (x,y)

        print(len(color_joined_pieces))
        acol_list=self.get_list_of_colors(color_joined_pieces)
        
        #is already sorted by colors!!!!
        #print(len(acol_list))
        #print(acol_list)

        return color_joined_pieces

    def get_list_of_colors(self,color_joined_pieces):
        col_list=[]
        sss=0
        lenlist=len(color_joined_pieces.items())
        for color, shapes in color_joined_pieces.items():
            if self.killer_event.is_set():
                break
            self.improcess_percentage=self.Set_Progress_Percentage(sss,lenlist,self.Pbarini,self.Pbarend)
            sss=sss+1
            if self.is_color_in_list(color,col_list)==False:
                col_list.append(color)
        return col_list
            

    def is_color_in_list(self,acolor,alist):        
        for ccc in alist:
            if self.is_same_color(ccc,acolor):
                return True
        return False
            
    def is_same_color(self,color1,color2):        
        lenc=len(color1)
        for iii in range(0,lenc):
            if(color1[iii]!=color2[iii]):
                return False
        return True
            
    '''
    def Sort_color_joined_pieces_to_radial(self,color_joined_pieces,xp=0,yp=0,rmin=5):
        lenlist=len(color_joined_pieces.items())
        r2list=[]
        sss=0        
        rmin2=rmin*rmin
        
        #((175, 78, 0, 255), [[[((225, 156), (224, 156)), ((224, 156), (224, 158)), ((224, 158), (225, 158)), ((225, 158), (225, 156))]]])
        
        #shapes=color_joined_pieces[color] # dictionary of colors
        #shape=shapes[0]
        #xylinesegments=shape[0]
        #one_xylinesegment=xylinesegments[0] #two (x,y) points
        #xytuple=one_xylinesegment[0]
        def byr2(eee):
            return eee['r2']
        print(len(color_joined_pieces))
        nnn=0
        new_color_joined_pieces={}
        xmin=100000000
        xmax=-100000000
        ymin=1000000000
        ymax=-100000000
        for color, shapes in color_joined_pieces.items():
            #num_shapes=len(shapes)
            if nnn==0:
                firstxytuple=shapes[0][0][0][0]
                (xp, yp)=firstxytuple            
            
            jjj=0
            for shape in shapes:
                for sub_shape in shape:
                    xytuple=sub_shape[0][0]                
                    (x, y)=xytuple
                    #print(x,y,xmin,xmax,ymin,ymax)
                    if x>xmax:
                        xmax=x
                    elif x<=xmin:
                        xmin=x    
                    if y>ymax:
                        ymax=y
                    elif y<=ymin:
                        ymin=y                  
                #calculate distance
                #r2=(x-xp)*(x-xp)+(y-yp)*(y-yp)                                                            
                #index_shape_list.append({'iii':iii,'jjj':jjj,'r2':r2})                
                jjj=jjj+1
        print(xmin,xmax,ymin,ymax)
        for color, shapes in color_joined_pieces.items():
            new_shapes=[]
            divisions=16
            deltax=-(xmin-xmax)/divisions
            deltay=-(ymin-ymax)/divisions
            for xxx in range(1,divisions+1):
                for yyy in range(1,divisions+1):                    
                    rminx=xmin + (xxx-1)*deltax
                    rmaxx=xmin + (xxx)*deltax
                    rminy=ymin + (yyy-1)*deltay
                    rmaxy=ymin + (yyy)*deltay  
                    #print(rminx,rmaxx,rminy,rmaxy)                  
                    for shape in shapes:
                         for sub_shape in shape:
                            xytuple=sub_shape[0][0]                
                            (x, y)=xytuple                        
                            if ((x>=rminx and x<rmaxx) and (y>=rminy and y<rmaxy)) or ((xxx==divisions or yyy==divisions) and (x>=rminx and x<=rmaxx) and (y>=rminy and y<=rmaxy)):
                                new_shapes.append(shape)

                
            if nnn<10:                
                print(len(shapes),len(new_shapes))
                #print(nnn,'Not Sorted ->',index_shape_list)
                #r2list.sort(key=byr2)
                #print(nnn,'    Sorted ->',index_shape_list)                                
                #print(nnn,' List',index_shape_list)

            new_color_joined_pieces[color] = new_shapes                
            nnn=nnn+1
        print('did ->',nnn)
        #print(color_joined_pieces.items())
        
        xylinesegments=shapes[0][0]
        print(xylinesegments)
        one_xylinesegment=shapes[0][0][0]
        print(one_xylinesegment)
        xytuple=shapes[0][0][0][0]
        print(xytuple)
        #make_err=color_joined_pieces.items(1)
        
        
                    
        
        # sort the list  internal functions to use sort  
        def byr2(eee):
            return eee['r2']
        def byx(eee):
            return eee['x']
        def byy(eee):
            return eee['y']
        def byrrr(eee):
            return eee['rrr']
        #it already does x0 -> ymax -> y min -> x+dx-> 
        r2list.sort(key=byr2)
        #for sitem in r2list:

        
        for color, shapes in color_joined_pieces.items():
            if self.killer_event.is_set():
                break
            self.improcess_percentage=self.Set_Progress_Percentage(sss,lenlist,self.Pbarini,self.Pbarend)
            sss=sss+1            
            for shape in shapes:  
                for sub_shape in shape:
                    here = sub_shape.pop(0)[0]
                    (x, y)=here
                    r2=(x-xp)*(x-xp)+(y-yp)*(y-yp)
                     
                    rrr=rrr+1   
        
        return new_color_joined_pieces      
    '''
    

    def Save_svg_text_file(self,svg_image,Filename):
        with open(Filename, "w") as text_file:
            text_file.write(svg_image)

def main():
    #imageRGBA = Image.open('test/examples/angular.png').convert('RGBA')
    imageRGBA = Image.open(r'C:\Users\FedericoGarcia\Documents\Wi Tonyswork\02_Gitfolders\tools\xyz Gui V2\src\img\User-Interface-Checked-Checkbox-icon.png').convert('RGBA')    
    print('Processing image of size',imageRGBA.size)    
    kill_ev = threading.Event()
    kill_ev.clear()
    Vectorize=Vectorization(imageRGBA,kill_ev)
    Vectorize.start()
    Vectorize.printprocess=True
    svg_image = Vectorize.rgba_image_to_svg_contiguous(im=imageRGBA)
    #svg_image = rgba_image_to_svg_pixels(image)
    Filename=r"C:\Users\FedericoGarcia\Documents\Wi Tonyswork\02_Gitfolders\tools\xyz Gui V2\src\toadd\test2.svg"
    Vectorize.Save_svg_text_file(svg_image,Filename)
    #with open("test/examples/angular.svg", "w") as text_file:
    #    text_file.write(svg_image)
    Vectorize.join()
        

if __name__ == '__main__':
    main()
