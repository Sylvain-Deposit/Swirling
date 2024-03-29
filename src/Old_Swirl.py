# -*- coding: utf-8 -*-
"""
Éditeur de Spyder

Ceci est un script temporaire.
"""
import warnings
import graphviz
import matplotlib.pyplot as plt
from matplotlib import patches as MatplotPatches
import numpy as np

from distributions import Spiral, Parametric, Circular
import Chatoyant

from moviepy.editor import VideoClip
from moviepy.video.io.bindings import mplfig_to_npimage

class Tools:
    def __init__(self):
        pass
    
    @staticmethod
    def _cart_to_pol(x, y):
        # convert cartesian coordinates to polar.
        r = np.sqrt(x ** 2 + y ** 2)
       
        theta = np.where(y >= 0, np.arccos(x / r), -np.arccos(x / r))
 
        return r, theta
    
    @staticmethod
    def _pol_to_cart(r, theta):
        # Convert polar coordinates to cartesian.
        x = r * np.cos(theta)
        y = r * np.sin(theta)
 
        return x, y
    
    def _scale(self, x, y, size):
        r, theta = self._cart_to_pol(x, y)
        r *= size
        x, y = self._pol_to_cart(r, theta)
        
        return x, y
        

#%% Anchor Class
class Anchor(object):
    instances = 0
    def __init__(self,
                 x, y,
                 parent = None,
                 name:str = None,
                 childs = []):
        
        self.x = x
        self.y = y
                   
        self.childs = []
        if isinstance(childs, Anchor):
            self.childs.append(childs)
            
        elif isinstance(childs, list) & all([isinstance(c, Anchor) for c in childs]):
                self.childs += childs
        else:
            raise TypeError('Childs must be a Anchor or list of Anchor objects')
        
        # Just in case...
        if isinstance(name, str):
            self.name = name
        else:
            self.name = f'Anchor-{Anchor.instances}'
            
        self.is_drawable = False
        Anchor.instances += 1
        
        
    def __sub__(self, other:'Anchor'):
        ### to test
        try:
            idx = self.childs.index(other)
            del self.childs[idx]
            
        except ValueError:
            warnings.warn('The element was not found in the list of childs')
            
        return self
    
    def __gt__(self, other):
        if isinstance(other, Anchor):
            self.childs.append(other)
            
            return self # returning self so we can chain the >
        
        if isinstance(other, list) & all([isinstance(c, Anchor) for c in other]):
            self.childs += other
            
            return self
            
        else:
            raise TypeError(f'Undefined operand between {type(self)} and {type(other)}.')
                        
    def _update_positions(self, childs, a, b):
        # Recursive function to update the position of all the childs of the object.
        if childs:
            for c in childs:
                c.x += a
                c.y += b
                
                self._update_positions(c.childs, a, b)
    
    def move_by(self, a, b):
        # Relative method to move the object and its childs
        self.x += a
        self.y += b
        
        self._update_positions(self.childs, a, b)
        
    def move_to(self, a, b):
        # Absolute method to move the object to the desired position, 
        # and update the childs accordingly.
        a -= self.x
        b -= self.y
        
        self.move_by(a, b)
        
    def at(self, other, link=False, merge=False):
        if not isinstance(other, Anchor):
            raise TypeError('Reference object must be a Anchor, received {type(other)}')
            
        self.move_to(other.x, other.y)
        
        if link:
            other.childs.append(self)
        
            
        
    def rotate_by(self, angle):
        # Method to rotate the obeject by any desired angle and update its childs.
        # Angle must be in degrees, converting to radians first
        angle = angle / 180 * np.pi
        
        # let's remember where the object was
        orig_x = self.x
        orig_y = self.y
        
        # Going to scene origin
        self.move_by(-orig_x, -orig_y)
        
        # Rotating the position of all the childs and updating their own childs
        for c in self.childs:
            r, theta = Tools._cart_to_pol(c.x, c.y)
            theta += angle
            x, y = Tools._pol_to_cart(r, theta)
            
            c.move_by(x-c.x, y-c.y)
            
        # Back to original position    
        self.move_by(orig_x, orig_y)
        
    def scale(self, size):
        # Same principle as rotation
        orig_x = self.x
        orig_y = self.y
        
        self.move_by(-orig_x, -orig_y)
        
        for c in self.childs:
            r, theta = Tools._cart_to_pol(c.x, c.y)
            r *= size
            x, y = Tools._pol_to_cart(r, theta)
            
            c.move_by(x-c.x, y-c.y)
             
        self.move_by(orig_x, orig_y)
        
    
        
        
        
#%% Drawabe Base Class
class Drawable(object):
    # All methods and attributes for is_drawable objects.
    
    def __init__(self, 
                 color = 'black',
                 fill = True,
                 size = 20,
                 alpha = 1,
                 linewidth = 5,
                 linecolor = 'black',
                 facecolor = 'red',
                 is_drawable = True):
        
        self.color = color
        self.size = size
        self.alpha = alpha
        self.linewidth = linewidth
        self.fill = fill
        self.facecolor = facecolor
        self.linecolor = linecolor
        self.is_drawable = is_drawable
        
        
    def _broadcast_values(self, values, n=100):
        
        if isinstance(values, np.ndarray):
            if values.size < n:
                return np.resize(values, n)
        if not isinstance(values, (list, np.ndarray)):
            values = [values]
        if len(values) < n:
            values = values * (n // len(values))
            
        return values
        
        
#%% All the drawables
class Point(Anchor, Drawable):
    instances = 0
    
    def __init__(self,
                 x, y,
                 parent = None,
                 name = None,
                 childs = [],
                 color = 'black',
                 size = 20,
                 alpha = 1):
        
        # Need unique names for the graph display
        if name is None:
            name = f'Point-{Point.instances}'
            
        Point.instances += 1
      
        Anchor.__init__(self, x, y, name = name, childs = childs)
        Drawable.__init__(self, color = color, size = size, alpha = alpha)
        
        
    def __repr__(self):
        return f'Point {self.name} at {self.x, self.y}'
    
    def __add__(self, other):
        if isinstance(other, Point):
            return Scatter([self.x, other.x], [self.y, other.y], 
                           name = self.name + '-' + other.name,
                           childs = self.childs.append(other.childs))
        
        raise TypeError('Only a Point can be added to another Point')
        
    
class Line(Anchor, Drawable):
    instances = 0
    
    def __init__(self,
                 xs, ys,
                 parent = None,
                 name = None,
                 color = 'black',
                 linewidth = 5,
                 alpha = 1
                ):
    
        
        # Need unique names for the graph display
        if name is None:
            name = f'Point-{Line.instances}'
            
        Anchor.__init__(self, xs, ys, name = name, childs = [])
        Drawable.__init__(self, color = color, linewidth = linewidth, alpha = alpha)
            
        Line.instances += 1
        self.is_drawable = True
                
    def __repr__(self):
        return f'Line made of {len(self.x)} points.'
    
    
    
class Scatter(Anchor):
    instances = 0
    
    def __init__(self,
                 xs, ys,
                 parent = None,
                 name = None,
                 childs = [],
                 colors = None):
        
        # Need unique names for the graph display
        if name is None:
            name = f'Scatter-{Scatter.instances}'
            
        Scatter.instances += 1
        
        if isinstance(childs, Point):
            childs = [childs]
   
        for x, y, c in zip(xs, ys, colors):
            
            childs.append(Point(x, y, color = c, childs=[]))
            
        Anchor.__init__(self, np.mean(xs), np.mean (ys), name = name, childs = childs)
        

    def __repr__(self):
        return f'Scatter {self.name} with {len(self.childs)} points.'
    
    def __add__(self, other):
        if isinstance(other, (Point, Scatter)):
            self.x.append(other.x)
            self.y.append(other.y)         
            self.childs.append(other.childs)
            
            return self
        
        raise TypeError('Only a Point or Scatter can be added to another Scatter')
        
class Polygon(Anchor, Drawable):
    instances = 0
    
    def __init__(self, n, size=1,
                 polygon_type = 'regular', 
                 
                 xs = None, 
                 ys = None,
                 parent = None,
                 name = None,
                 childs = [],
                 facecolor = 'red',
                 linecolor = 'black',
                 linewidth = 3,
                 alpha = 1,
                 is_drawable=True):
        
        if (polygon_type == 'regular') & (n is not None):
            xs, ys = Circular(n).uniform()
        
        else:
            if (xs is None) | (ys is None):
                raise ValueError('If the polygon is not regular, you must input x & y coordinates.')

        if name is None:
            name = f'Polygon-{Polygon.instances}'
            
        if isinstance(parent, Anchor):
            Anchor.__init__(self, parent.x, parent.y, name = name, childs = childs)
            parent.childs.append(self)
            
        else:
            Anchor.__init__(self, np.mean(xs), np.mean (ys), name = name, childs = childs)
        
        Drawable.__init__(self, facecolor=facecolor, linecolor=linecolor, linewidth=linewidth, alpha = alpha, is_drawable=is_drawable)
        
        for x, y in zip(xs, ys):
            
            self.childs.append(Anchor(x, y, childs=[]))
            
        self.scale(size)
        
        Polygon.instances += 1
        
        
    def test(self):
        return 'test'
        
        
   
#%% Scene class        
class Scene(Anchor):
    def __init__(self, 
                 name:str = 'Scene', 
                 childs = []):
        
        super().__init__(0, 0, name = name, childs = childs)
        
    def __repr__(self):
        return f'Scene {self.name} with {len(self.childs)} direct child(s).'        
    
    
    def add_node(self, dot, parent, childs, verbose=False):
        
        
        if childs:
            for child in childs:
                dot.attr('node', shape='plaintext', fontsize="10pt", beautify='true')
                
                if isinstance(child, Point):
                    dot.attr('node', shape='circle', fontsize="10pt", beautify='true')
                    
                elif isinstance(child, Polygon):
                    dot.attr('node', shape='polygon', fontsize="10pt", beautify='true')
                    
                    
                child_name = child.name
                if verbose:
                    child_name = child.__repr__()
                    
                dot.node(child_name)
                dot.edge(parent, child_name)
                # Yay, recursion!
                self.add_node(dot, child_name, child.childs, verbose=verbose)
        
    def show_hierarchy(self, name='test', verbose=False):
        dot = graphviz.Digraph(f'Hierarchy view for {self.name} scene', 
                               format='svg', 
                               )
        # Scene first
        dot.attr('node', shape='diamond')
        dot.node(self.name)
        self.add_node(dot, self.name, self.childs, verbose=verbose)
        
        dot = dot.unflatten()
        
        dot.render(name)
       
    def _draw_point(self, ax, point, **kwargs):
     
        ax.scatter(point.x, 
                   point.y, 
                   color = point.color, 
                   s = point.size, 
                   alpha = point.alpha)
        
    def _draw_line(self, ax, line):
        ax.plot(line.xs, 
                line.ys, 
                color = line.color, 
                linewidth = line.linewidth, 
                alpha = line.alpha)
        
    def _draw_polygon(self, ax, poly):
        xy = [[c.x, c.y] for c in poly.childs]
        poly = MatplotPatches.Polygon(xy,
                                      facecolor = poly.facecolor,
                                      edgecolor = poly.linecolor, # Matplotlib constantly swings between linecolor and edgecolor :(
                                      linewidth = poly.linewidth,
                                      alpha = poly.alpha,
                                      antialiased = True,
                                      fill = poly.fill)
        ax.add_patch(poly)
        
        
    def _draw_verbose(self, ax, parent, child):
        if child.is_drawable == False:
            ax.scatter(child.x, child.y, color='black', marker='+', s=100)
        ax.arrow(parent.x,
                 parent.y, 
                 child.x - parent.x,
                 child.y - parent.y,
                 color = 'red', 
                 linewidth = 0.2,
                 linestyle = '--',
                 alpha = 0.5,
                 width = 0.01,
                 length_includes_head = True)
        
        ax.text(child.x, child.y, child.name, fontsize=10)
        
    
    def draw_elements(self, ax, parent, childs, verbose=False):
        if childs:
            for child in childs:
                if child.is_drawable:
                    if isinstance(child, Point):
                        self._draw_point(ax, child)
                        
                    if isinstance(child, Line):
                        self._draw_line(ax, child)
                        
                    if isinstance(child, Polygon):
                        self._draw_polygon(ax, child)
                        
                if verbose:
                    self._draw_verbose(ax, parent, child)
                    
                # Yay, recursion (bis)
                self.draw_elements(ax, child, child.childs, verbose=verbose)
        
    def quick_display(self, verbose=False):
        fig, ax = plt.subplots(figsize=(8,8), ncols=1, nrows=1)
        ax.set_xlim(-5, 5)
        ax.set_ylim(-5, 5)
        
        if verbose:
            ax.scatter(self.x, self.y, color='black', marker='+', s=100)
            ax.text(self.x, self.y, self.name, fontsize=10)
            ax.axis('on')
            ax.grid(which='both')
                    
        self.draw_elements(ax, self, self.childs, verbose=verbose)
        
        fig.suptitle(self.name)
        fig.tight_layout(pad=1.2)
        
    def render(self, ax):
        self.draw_elements(ax, self, self.childs, verbose=False)

#%% Main
if __name__ == '__main__':
    
    scene = Scene()
    
    root = Polygon(4, size=2)
    root.is_drawable = False

    scene > root    
    for c in root.childs:
        new = Polygon(4, size=2, linewidth=1)
        # new.rotate_by(45)
        new.at(c, link=True)
    
    # scene.quick_display()
 
    fig, ax = plt.subplots(nrows=1, ncols=1, figsize=(4,4))
    
    def make_frame(t):
        ax.clear()
        ax.axis('off')
        ax.set_xlim(-4, 4)
        ax.set_ylim(-4, 4)
        
        scene.render(ax)
       
        if 0<t<1:
            root.rotate_by(4.5)
        
        if 1 <= t <=2 :
            for c in root.childs:
                c.childs[0].rotate_by(-4.5)
        
        return mplfig_to_npimage(fig)
    
    
    # animation = VideoClip(make_frame, duration=2)
    # animation.write_gif('matplotlib.gif', fps=20)
    
    scene.show_hierarchy('scene')
   
   

        
    

      
        