# -*- coding: utf-8 -*-
"""
Éditeur de Spyder

Ceci est un script temporaire.
"""
import warnings
# import graphviz
import matplotlib.pyplot as plt
from matplotlib import patches as MatplotPatches
import numpy as np

from .distributions import Spiral, Parametric, Circular
from .functions import Distance
from . import Chatoyant

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
                 name:str = None,
                 childs = None,
                 drawables = None,
                 ):
        
        self.x = x
        self.y = y
        
        self.drawables = [] 
        if drawables is not None:
            
            if isinstance(drawables, Drawable):
                self.drawables.append(drawables)
            elif isinstance(drawables, list) & all([isinstance(d, Drawable) for d in drawables]):
                    self.drawables += drawables
            else:
                raise TypeError('Drawables must be a Drawable or list of Drawable objects.')
                   
        self.childs = []
        
        if childs is not None:
            if isinstance(childs, Anchor):
                self.childs.append(childs)
            elif isinstance(childs, list) & all([isinstance(c, Anchor) for c in childs]):
                    self.childs += childs
            else:
                raise TypeError('Childs must be an Anchor or list of Anchor objects')
        
        # Just in case...
        self.name = name if isinstance(name, str) else f'Anchor-{Anchor.instances}'
       
        Anchor.instances += 1
        
    def __repr__(self):
        return f'Anchor {self.name} at {self.x:3.2f}, {self.y:3.2f}'
        
        
    def __sub__(self, other:'Anchor'):
        ### to test
        try:
            idx = self.childs.index(other)
            del self.childs[idx]
            
        except ValueError:
            warnings.warn('The element was not found in the list of childs')
            
        return self
    
    def __gt__(self, other):
        # Not really working, to check.
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
        
    def _apply_polar_transform(self, angle=0, size=1):
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
            r *= size
            x, y = Tools._pol_to_cart(r, theta)
            
            c.move_by(x-c.x, y-c.y)
            
        # Back to original position    
        self.move_by(orig_x, orig_y)
        
    def rotate_by(self, angle):
        self._apply_polar_transform(angle=angle)
        
    def scale_by(self, size):
        self._apply_polar_transform(size=size)
        
    def rotate_drawables_by(self, angle):
        if self.drawables is not None:
            for d in self.drawables:
                d.rotate_by(angle)
                
    def scale_drawables_by(self, size):
        if self.drawables is not None:
            for d in self.drawables:
                d.scale_by(size)
        
        
 
        
    
        
        
        
#%% Drawabe Base Class
class Drawable(object):
    instances = 0
    # All methods and attributes for drawable objects.
    
    def __init__(self,
                 x, y,
                 name = None,
                 
                 color = 'black',
                 fill = True,
                 size = 20,
                 alpha = 1,
                 linewidth = 5,
                 linecolor = 'black',
                 facecolor = 'red',
                 ):
        
        self.x = x
        self.y = y

        self.name = name if isinstance(name, str) else f'Drawable-{Drawable.instances}'
        
        
        self.color = color
        self.size = size
        self.alpha = alpha
        self.linewidth = linewidth
        self.fill = fill
        self.facecolor = facecolor
        self.linecolor = linecolor
        
    def __repr__(self):
        return f'{self.name} at {np.mean(self.x):3.2f}, {np.mean(self.y):3.2f}'
      
        
    def at(self, anchor):
        if isinstance(anchor, Anchor):
            self.x -= np.mean(self.x)
            self.y -= np.mean(self.y)
            self.parent = anchor
            anchor.drawables.append(self)
         
        else:
            raise ValueError(f'Only Anchors are accepted, got {type(anchor)}')
   
    def move_by(self, a, b):
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
    
    def _apply_polar_transform(self, angle=0, size=1):
        # Method to rotate the drawables by any desired angle.
        # Angle must be in degrees, converting to radians first
        # Drawables are actually 0-centered then shifted to the anchor.
        angle = angle / 180 * np.pi
        
        orig_x = np.mean(self.x)
        orig_y = np.mean(self.y)

        self.move_by(- orig_x, - orig_y)
               
        r, theta = Tools._cart_to_pol(self.x, self.y)
        theta += angle
        r *= size
        x, y = Tools._pol_to_cart(r, theta)

        self.x = x
        self.y = y
       
        # Back to original position    
        self.move_by(orig_x, orig_y)
        
    
    def rotate_by(self, angle):
        self._apply_polar_transform(angle = angle)
        
    def scale_by(self, size):
        self._apply_polar_transform(size = size)

        

        
        
        
#%% All the drawables
class Point(Drawable):
    instances = 0
    
    def __init__(self,
                 x = 0, 
                 y = 0,
                
                 name = None,
                
                 color = 'black',
                 size = 20,
                 alpha = 1):
        
        # Need unique names for the graph display
        if name is None:
            name = f'Point-{Point.instances}'
            
        Point.instances += 1
      
        Drawable.__init__(self, x, y, name = name, color = color, size = size, alpha = alpha)
       
    def __repr__(self):
        return f'Point {self.name} at {self.x:3.2f}, {self.y:3.2f}'
            
    
            
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
        
    def __repr__(self):
        return f'Scatter of {len(self.x)} points.'
        
        
        
        
#%% Anchors
class Anchors(Anchor):
    instances = 0
    
    def __init__(self,
                 xs = [], 
                 ys = [],
                 name = None,
                ):
        
        # Need unique names for the graph display
        if name is None:
            name = f'Anchors-{Anchors.instances}'
        Anchors.instances += 1

        Anchor.__init__(self, np.mean(xs), np.mean (ys), name = name, childs = [], drawables = [])

        for x, y in zip(xs, ys):
            
            self.childs.append(Anchor(x, y))
   
            
    def __repr__(self):
        return f'Group {self.name} with {len(self.childs)} anchors.'
    
    
#%%    
class Polygon(Drawable):
    instances = 0
    
    def __init__(self, 
                 n, 
                 size=1,
                 polygon_type = 'regular', 
                 xs = None, 
                 ys = None,
                 name = None,
                 facecolor = 'red',
                 linecolor = 'black',
                 linewidth = 3,
                 alpha = 1,
                 fill = True
                 ):
        
        if (polygon_type == 'regular') & (n is not None):
            xs, ys = Circular(n).uniform()
            xs *= size
            ys *= size
        
        else:
            if (xs is None) | (ys is None):
                raise ValueError('If the polygon is not regular, you must input x & y coordinates.')

        if name is None:
            name = f'Polygon-{Polygon.instances}'
        
        Drawable.__init__(self, 
                          x = xs, 
                          y = ys, 
                          name = name,
                          facecolor = facecolor, 
                          linecolor = linecolor, 
                          linewidth = linewidth, 
                          alpha = alpha,
                          fill = fill)
        
        # self.rotate_by(180 / n)
                  
        Polygon.instances += 1
        
    def __repr__(self):
        return f'Polygon {self.name} with {len(self.x)} edges.'
    
class Circle(Drawable):
    instances = 0
    def __init__(self, x = 0, 
                 y = 0,
                 radius = 1,
                 name = None,
                 facecolor = 'red',
                 linecolor = 'black',
                 linewidth = 3,
                 alpha = 1,
                 fill = True):
        
        if name is None:
            name = f'Circle-{Circle.instances}'
        
        Drawable.__init__(self, 
                          x = x, 
                          y = y, 
                          name = name,
                          facecolor = facecolor, 
                          linecolor = linecolor, 
                          linewidth = linewidth, 
                          alpha = alpha,
                          fill = fill)
        
        self.radius = radius
        
        def __repr__(self):
            return f'Circle {self.name} at {self.x:3.2f}, {self.y:3.2f}'
        
        def rotate_by(self, angle):
            # Sneaky way to don't do anything when we rotate a circle
            pass
        
        def scale_by(self, scale):
            self.radius *= scale
            
        
        
        
        
   
#%% Scene class        
class Scene(Anchor):
    def __init__(self, 
                 name:str = 'Scene', 
                 childs = None, 
                 ):
        
        childs = childs if childs else []
        
        Anchor.__init__(self, name = name, childs = [])
        
    def __repr__(self):
        return f'Scene {self.name}, {len(self.childs)} child(s).'        
    
    
    def add_node(self, dot, parent, childs, verbose=False):
        
        
        dot.attr('node', shape='diamond')
        parent_name = parent.name
        
        if verbose:
            parent_name = parent.__repr__()
            
        dot.node(parent_name)

        
        if parent.drawables:
            for d in parent.drawables:
                dot.attr('node', shape='ellipse', fontsize="10pt", beautify='true')
                drawable_name = d.name
                if verbose:
                    drawable_name = d.__repr__()
                    
                dot.node(drawable_name)
                dot.edge(parent_name, drawable_name)
                    
        if childs:
            for child in childs:
                dot.attr('node', shape='plaintext', fontsize="10pt", beautify='true')
                                    
                if isinstance(child, Anchors):
                    dot.attr('node', shape='rectangle', fontsize="10pt", beautify='true')
            
                child_name = child.name
                if verbose:
                    child_name = child.__repr__()
                    
                dot.node(child_name)
                dot.edge(parent_name, child_name)
                
                # Yay, recursion!
                self.add_node(dot, child, child.childs, verbose=verbose)
        
    def show_hierarchy(self, name='test', verbose=False):
        dot = graphviz.Digraph(f'Hierarchy view for {self.name} scene', 
                               format='svg', 
                               )
        self.add_node(dot, self, self.childs, verbose=verbose)
        
        dot = dot.unflatten()
        
        dot.render(name)
       
    def _draw_point(self, ax, parent, point, **kwargs):
        
        ax.scatter(point.x + parent.x, 
                   point.y + parent.y, 
                   color = point.color, 
                   s = point.size, 
                   alpha = point.alpha,
                   **kwargs)
        
    def _draw_scatter(self, ax, parent, scatter, **kwargs):
            
        ax.scatter(scatter.x + parent.x, 
                   scatter.y + parent.y, 
                   color = scatter.color, 
                   s = scatter.size, 
                   alpha = scatter.alpha,
                   **kwargs)
        
                
    def _draw_polygon(self, ax, parent, poly, **kwargs):
        xy = [[parent.x + x, parent.y + y] for x, y in zip(poly.x, poly.y)]
        
        poly = MatplotPatches.Polygon(xy,
                                      facecolor = poly.facecolor,
                                      edgecolor = poly.linecolor, 
                                      linewidth = poly.linewidth,
                                      alpha = poly.alpha,
                                      antialiased = True,
                                      fill = poly.fill,
                                      **kwargs)
        ax.add_patch(poly)
        
    def _draw_circle(self, ax, parent, circle, **kwargs):
        xy = [parent.x + self.x, parent.y + self.y]
        circle = MatplotPatches.Circle(xy, 
                                       radius = circle.radius,
                                       facecolor = circle.facecolor,
                                       edgecolor = circle.linecolor, 
                                       linewidth = circle.linewidth,
                                       alpha = circle.alpha,
                                       antialiased = True,
                                       fill = circle.fill,
                                       **kwargs)
        ax.add_patch(circle)
        
    def _draw_arrows(self, ax, parent, child):
        ax.arrow(parent.x,
                 parent.y, 
                 child.x - parent.x,
                 child.y - parent.y,
                 color = 'red', 
                 linewidth = 0.2,
                 linestyle = ':',
                 alpha = 0.5,
                 width = 0.01,
                 length_includes_head = True)
        
    def _draw_anchors(self, ax, parent):
 
        ax.scatter(parent.x, parent.y, color='black', marker='+', s=100)
        ax.text(parent.x, parent.y, parent.name, fontsize=10)
        
        
    def _draw_drawables(self, ax, parent):

        for d in parent.drawables:
            
            if isinstance(d, Point):
                self._draw_point(ax, parent, d)
                
            if isinstance(d, Scatter):
                self._draw_scatter(ax, parent, d)
                
            if isinstance(d, Polygon):
                self._draw_polygon(ax, parent, d)
                
            if isinstance(d, Circle):
                self._draw_circle(ax, parent, d)
                
   
    def draw_elements(self, ax, parent, childs, verbose=False):
        if parent.drawables:
                self._draw_drawables(ax, parent)
        if verbose:
            self._draw_anchors(ax, parent)

        if childs:
            for child in childs:
                                
                if verbose:
                    self._draw_arrows(ax, parent, child)
                    
                # Yay, recursion (bis)
                self.draw_elements(ax, child, child.childs, verbose=verbose)
        
    def quick_display(self, verbose=False):
        fig, ax = plt.subplots(figsize=(8,8), ncols=1, nrows=1)
        
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


def hexagons():
    duration = 3
    fps = 50
    n_points = 150
    x, y = Parametric(n=n_points).sunflower(alpha=1)
    x *= 4
    y *= 4
    
    sizes = Distance(x, y).normal(sd=5) + 0.2
 
    # sizes = sizes[::-1]
    colors = Chatoyant.ColorMap().from_matplotlib('inferno', n=n_points//2)
    colors = (colors + colors.invert()).map_to_index(sizes)
    
    scene = Scene()
    
    anchors = Anchors(x, y)
    scene > anchors
    
    
    
    for a, c, s in zip(anchors.childs, colors.to_float_list(), sizes):
        p = Polygon(6, linewidth=0, alpha = 0.8, size=s, facecolor=c)
        p2 = Polygon(6, linewidth=0, alpha = 1, size=s/3, facecolor=c)

        a.drawables = [p, p2]
               
    fig, ax = plt.subplots(nrows=1, ncols=1, figsize=(4,4), dpi=75)
    

    def make_frame(t):
        
        ax.clear()
        ax.axis('off')
        ax.set_xlim(-4, 4)
        ax.set_ylim(-4, 4)
        
        
        scene.render(ax)
        
        idx = int(t * fps)
        cmap = colors.roll(idx).to_float_list()
        anchors.rotate_by(3.6)

        for a, c in zip(anchors.childs, cmap):
            for d in a.drawables:
                
                d.facecolor = c
                
        fig.tight_layout(pad=0.8)
        return mplfig_to_npimage(fig)
    

    animation = VideoClip(make_frame, duration=duration)
    animation.write_gif('hexagons.gif', fps=fps)
    
def rotating_squares():
    scene = Scene()
    
    root = Anchors(*Circular(4).uniform())
    root.scale_by(2)
    

    scene > root    
    for c in root.childs:
        c.drawables = [Polygon(4, size=2, linewidth=1)]
        
     
    fig, ax = plt.subplots(nrows=1, ncols=1, figsize=(2, 2), dpi=75)
    
    def make_frame(t):
        ax.clear()
        ax.axis('off')
        ax.set_xlim(-4, 4)
        ax.set_ylim(-4, 4)
        
        scene.render(ax)
       
        if 0 < t < 1:
            root.rotate_by(4.5)
        
        if 1 <= t <=2 :
            for c in root.childs:
                c.rotate_drawables(-4.5)
                
        fig.tight_layout(pad=0.2)
        return mplfig_to_npimage(fig)
    
    animation = VideoClip(make_frame, duration=2)
    animation.write_gif('rotating_squares.gif', fps=20, verbose=True)
    



#%% Main
if __name__ == '__main__':
    scene = Scene()
    root = Anchor()
    scene > root
          
    fig, ax = plt.subplots(nrows=1, ncols=1, figsize=(2, 2), dpi=75)
    
    def make_frame(t):
        ax.clear()
        ax.axis('off')
        ax.set_xlim(-1, 1)
        ax.set_ylim(-1, 1)
        
        scene.render(ax)
        c = np.random.uniform(0, 1)
        if c > 0.8:
            x = np.random.uniform(-1, 1)
            y = np.random.uniform(-1, 1)
            p = Anchor(x, y)
            root > p
            
            p.drawables.append(Circle(radius=0.05, linewidth=0))

        root.rotate_by(2)
        
       
        # scene.quick_display(verbose=True)        
        fig.tight_layout(pad=0.2)
        
        
        return mplfig_to_npimage(fig)
    
    # t = make_frame(1)
    # plt.imshow(t)
    
    animation = VideoClip(make_frame, duration=5)
    animation.write_gif('Appearing_points.gif', fps=40)
    
    
    
    
    
    # scene.show_hierarchy(verbose = True)
    # scene.quick_display(verbose=False)
    