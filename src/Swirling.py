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
                 x = 0, 
                 y = 0,
                 parent = None,
                 name:str = None,
                 childs = [],
                 drawables = [],
                 element = 'anchor'):
        
        self.x = x
        self.y = y
        self.element = element
        self.drawables = drawables
                   
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
            self.childs += [other]
            
            return self
        
        elif isinstance(other, Anchors):
              
            self.childs += other.childs
            return self
                
           
        
        elif isinstance(other, Drawable):
                        
            self.drawables += [other]
            
            return self
        
        elif isinstance(other, list) & all([isinstance(c, Anchor) for c in other]):
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
    
    def _move_drawables(self, a, b):
        print('Moving drawables!')
    
    def move_by(self, a, b):
        # Relative method to move the object and its childs
        self.x += a
        self.y += b
        
        self._update_positions(self.childs, a, b)
        if self.drawables:
            self._move_drawables(a, b)
        
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
 
        
    
        
        
        
#%% Drawabe Base Class
class Drawable(object):
    # All methods and attributes for drawable objects.
    
    def __init__(self,
                 x, y,
                 name = None,
                 parent = Anchor(0, 0),
                 color = 'black',
                 fill = True,
                 size = 20,
                 alpha = 1,
                 linewidth = 5,
                 linecolor = 'black',
                 facecolor = 'red',
                 element = 'point',
                 is_drawable = True):
        
        self.x = x
        self.y = y
        self.name = name
        self.parent = parent
        self.childs = []
        self.color = color
        self.size = size
        self.alpha = alpha
        self.linewidth = linewidth
        self.fill = fill
        self.facecolor = facecolor
        self.linecolor = linecolor
        self.is_drawable = is_drawable
        self.element = element
        
    def at(self, anchor):
        
        if isinstance(anchor, Anchor):
            self.x -= np.mean(self.x)
            self.y -= np.mean(self.y)
            self.parent = anchor
            anchor.drawables.append(self)
            
            
            
        else:
            raise ValueError(f'Only Anchors are accepted, got {type(anchor)}')
   
    def shift_by(self, a, b):
        self.x += a
        self.y += b
        
        return self
        
        
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
class Point(Drawable):
    instances = 0
    
    def __init__(self,
                 x = 0, 
                 y = 0,
                 parent = None,
                 name = None,
                
                 color = 'black',
                 size = 20,
                 alpha = 1):
        
        # Need unique names for the graph display
        if name is None:
            name = f'Point-{Point.instances}'
            
        Point.instances += 1
      
        Drawable.__init__(self, x, y, name = name, color = color, size = size, alpha = alpha)
        self.parent = parent
        
        
    def __repr__(self):
        return f'Drawable point {self.name} at {self.x, self.y}'
            
    
            
        
#%%    
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
#%%    
class Scatter(Drawable):
    instances = 0
    def __init__(self,
                 xs, ys,
                 size = 10,
                 name = None,
                 color = 'black',
                
                 alpha = 1):

        if name is None:
            name = f'Scatter-{Scatter.instances}'
        
        color = self._broadcast_values(color, len(xs))
        alpha = self._broadcast_values(alpha, len(xs))
        size = self._broadcast_values(size, len(xs))
        
        Drawable.__init__(self, xs, ys, color = color, size = size, alpha = alpha)
            
        Scatter.instances += 1
        
        
        
        
#%% Anchors
class Anchors(Anchor):
    instances = 0
    
    def __init__(self,
                 xs = [], 
                 ys = [],
                
                 name = None,
                 
                 colors = 'red',
                ):
        
        # Need unique names for the graph display
        if name is None:
            name = f'Anchor-{Anchors.instances}'
        Anchors.instances += 1
            
        
        
        Anchor.__init__(self, np.mean(xs), np.mean (ys), name = name, childs = [], drawables = [])

        for x, y in zip(xs, ys):
            
            self.childs.append(Anchor(x, y, childs=[]))
   
            
    def __repr__(self):
        return f'Scatter {self.name} with {len(self.childs)} {self.element} elements.'
    
    
#%%    
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
                 childs = [], 
                 ):
        
        Anchor.__init__(self, name = name, childs = childs)
        
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
       
    def _draw_point(self, ax, parent, point, **kwargs):
        
        ax.scatter(point.x + parent.x, 
                   point.y + parent.y, 
                   color = point.color, 
                   s = point.size, 
                   alpha = point.alpha)
        
    def _draw_scatter(self, ax, parent, scatter, **kwargs):
        print('drawing scatter')
        
        ax.scatter(scatter.x + parent.x, 
                   scatter.y + parent.y, 
                   color = scatter.color, 
                   s = scatter.size, 
                   alpha = scatter.alpha)
        
        
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

        if isinstance(child, Anchor):
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
        
    def _draw_drawables(self, ax, parent, drawable_list):

        for d in drawable_list:
            
            if isinstance(d, Point):
                self._draw_point(ax, parent, d)
                
            if isinstance(d, Scatter):
                self._draw_scatter(ax, parent, d)
                
   
    def draw_elements(self, ax, parent, childs, verbose=False):
        if parent.drawables:
    
                self._draw_drawables(ax, parent, parent.drawables)

        if childs:
            for child in childs:
                                
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

        plt.show()
        
    def render(self, ax):
        self.draw_elements(ax, self, self.childs, verbose=False)

#%% Main
if __name__ == '__main__':
    x, y = Parametric(n=30).sunflower(alpha=1)
    
    scene = Scene()
    
    root = Anchor(1, 0.5)
    root2 = Anchor(2, 2)
    
    scene.childs = [root]
    root.childs = [root2]
    
    
    Scatter(x, y, color=['black', 'red'], size=20)
    root.drawables = [Scatter(x, y, color=['black', 'red'], size=20)]
        
    # Point(color='red', size=50).at(s)
    # p.at(root)

    #♣ root > s
    
    
    
    
    # root.drawables = [s]
    # scene.rotate_by(90)
    
    
    scene.quick_display(verbose=True)
    
    

    
   
   

        
    

      
        