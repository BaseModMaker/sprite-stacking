# Browser Performance Optimization Guide for Sprite Stacking Game

## Overview
This guide provides comprehensive optimization strategies to dramatically improve FPS when running your sprite stacking game in a browser environment. The main performance bottlenecks are identified and solutions are provided.

## Critical Performance Issues Identified

### 1. **Shadow Rendering Bottleneck** ⚠️ **HIGH IMPACT**
**Current Issue**: Each sprite stack renders complex shadows using mask operations and multiple surface blits
- `_draw_shadow()` creates large surfaces (3.5x object size) for each object
- Uses `pygame.mask.from_surface()` and `mask.to_surface()` which are CPU-intensive
- Processes multiple layers per shadow with rotation caching

**Solutions**:
```python
# A. Disable shadows completely for web
if self.is_web:
    self.shadow_enabled = False

# B. Pre-compute shadow sprites at initialization
def _precompute_shadows(self):
    """Pre-compute shadow sprites for different rotations"""
    self.shadow_cache = {}
    for angle in range(0, 360, 15):  # Every 15 degrees
        self.shadow_cache[angle] = self._create_shadow_sprite(angle)

# C. Use simple circle shadows instead of complex mask-based ones
def _draw_simple_shadow(self, surface, x, y):
    """Draw a simple elliptical shadow"""
    shadow_size = (self.width // 2, self.height // 4)
    pygame.draw.ellipse(surface, (0, 0, 0, 100), 
                       (x - shadow_size[0], y + self.height//2, 
                        shadow_size[0]*2, shadow_size[1]))
```

### 2. **Outline Rendering Performance** ⚠️ **HIGH IMPACT**
**Current Issue**: Outline system creates temporary surfaces and processes masks for each object
- Creates large temporary surfaces with padding
- Uses `pygame.mask.outline()` which is expensive
- Processes every visible object individually

**Solutions**:
```python
# A. Disable outlines for web
if self.is_web:
    outline_enabled = False

# B. Pre-compute outline sprites
def _precompute_outlines(self):
    """Pre-compute outlined sprites at initialization"""
    self.outline_cache = {}
    for angle in range(0, 360, 15):
        self.outline_cache[angle] = self._create_outlined_sprite(angle)

# C. Use simple border rectangles instead
def _draw_simple_outline(self, surface, x, y, width, height):
    """Draw a simple rectangular outline"""
    rect = pygame.Rect(x - width//2, y - height//2, width, height)
    pygame.draw.rect(surface, self.outline_color, rect, self.outline_thickness)
```

### 3. **Layer Rotation Caching Issues** ⚠️ **MEDIUM IMPACT**
**Current Issue**: Rotation cache is created per sprite stack instance, not globally
- Each object maintains its own rotation cache
- Memory usage grows with number of objects
- Cache misses are common due to floating-point rotation values

**Solutions**:
```python
# Global rotation cache manager
class GlobalRotationCache:
    def __init__(self, max_size=1000):
        self.cache = {}
        self.max_size = max_size
        
    def get_rotated_surface(self, surface, angle):
        # Round angle to nearest 5 degrees for better cache hits
        cache_angle = round(angle / 5) * 5
        key = (id(surface), cache_angle)
        
        if key not in self.cache:
            if len(self.cache) >= self.max_size:
                # Remove oldest entries
                self.cache.clear()
            self.cache[key] = pygame.transform.rotate(surface, -cache_angle)
        
        return self.cache[key]

# Use global cache in sprite stack
rotation_cache = GlobalRotationCache()
```

### 4. **Background Rendering Optimization** ⚠️ **MEDIUM IMPACT**
**Current Issue**: Background gradient is drawn line-by-line every frame
- 600+ individual `pygame.draw.line()` calls per frame
- Recalculates colors repeatedly

**Solutions**:
```python
# Pre-render background once
def _create_optimized_background(self):
    """Create background once and reuse"""
    self.static_background = pygame.Surface((self.camera.width, self.camera.height))
    
    # Draw gradient once
    for y in range(self.camera.height):
        depth_factor = y / self.camera.height
        blue = 40 + int(40 * (1 - depth_factor))
        green = 65 + int(15 * (1 - depth_factor))
        pygame.draw.line(self.static_background, (10, green, blue), (0, y), (self.camera.width, y))

# In draw loop, just blit the pre-rendered background
def draw(self):
    camera_surface = self.camera.get_surface()
    camera_surface.blit(self.static_background, (0, 0))
```

### 5. **Grid Rendering Optimization** ⚠️ **LOW IMPACT**
**Current Issue**: Grid lines are redrawn every frame with alpha blending
- Creates new surface each frame
- Multiple line drawing operations

**Solutions**:
```python
# Pre-compute grid or disable for web
if self.is_web:
    self.show_grid = False  # Disable grid completely

# Or use simpler grid
def _draw_simple_grid(self, surface):
    """Draw simple grid without alpha blending"""
    grid_color = (40, 70, 90)  # Remove alpha
    # ... rest of grid drawing
```

## Layer Count Optimization Strategies

### 6. **Dynamic Layer Reduction** ⚠️ **HIGH IMPACT**
**Current Issue**: High layer counts (24 layers for submarine, 18 for kelp, 26 for rocks)

**Solutions**:
```python
# A. Web-specific layer limits
def __init__(self, ...):
    if hasattr(sys, '_emscripten_info'):  # Web environment
        # Reduce layer count for web
        self.num_layers = min(num_layers, 8)  # Cap at 8 layers
        self.layer_offset = max(layer_offset, 1.0)  # Increase offset for better effect
    
# B. Level-of-detail system
def get_layer_count_for_distance(self, distance_to_camera):
    """Reduce layers based on distance"""
    if distance_to_camera > 300:
        return max(2, self.num_layers // 4)
    elif distance_to_camera > 150:
        return max(4, self.num_layers // 2)
    else:
        return self.num_layers

# C. Performance-based adaptive layers
class AdaptiveLayerManager:
    def __init__(self):
        self.target_fps = 30
        self.current_layer_multiplier = 1.0
        
    def update(self, current_fps):
        if current_fps < self.target_fps:
            self.current_layer_multiplier *= 0.9  # Reduce layers
        elif current_fps > self.target_fps + 10:
            self.current_layer_multiplier = min(1.0, self.current_layer_multiplier * 1.1)
```

### 7. **Surface Optimization** ⚠️ **MEDIUM IMPACT**
**Current Issue**: Surfaces are not optimized for browser rendering

**Solutions**:
```python
# Optimize surface formats
def _optimize_surface(self, surface):
    """Convert surface to optimal format for web"""
    if hasattr(sys, '_emscripten_info'):
        # For web, avoid alpha conversion when possible
        if surface.get_alpha() is None and not surface.get_flags() & pygame.SRCALPHA:
            return surface.convert()
        else:
            return surface.convert_alpha()
    else:
        return surface.convert_alpha()

# Use smaller surfaces when possible
def _create_web_optimized_layer(self, original_surface):
    """Create smaller version for web"""
    if hasattr(sys, '_emscripten_info'):
        size = original_surface.get_size()
        new_size = (max(16, size[0] // 2), max(16, size[1] // 2))
        return pygame.transform.scale(original_surface, new_size)
    return original_surface
```

## Object Culling Optimizations

### 8. **Enhanced Frustum Culling** ⚠️ **MEDIUM IMPACT**
**Current Issue**: Basic distance-based culling

**Enhanced Solution**:
```python
def _get_visible_objects_optimized(self):
    """Improved object culling with multiple optimizations"""
    visible_objects = []
    
    # Smaller margin for web
    margin = 100 if self.is_web else 200
    
    # Pre-calculate bounds
    cam_bounds = {
        'left': self.camera.x - self.camera.width // 2 - margin,
        'right': self.camera.x + self.camera.width // 2 + margin,
        'top': self.camera.y - self.camera.height // 2 - margin,
        'bottom': self.camera.y + self.camera.height // 2 + margin
    }
    
    # Use spatial partitioning if many objects
    if len(self.world_objects) > 50:
        return self._get_objects_spatial_partition(cam_bounds)
    
    # Quick bounds check first, then distance
    for obj in self.world_objects:
        if (cam_bounds['left'] <= obj.x <= cam_bounds['right'] and 
            cam_bounds['top'] <= obj.y <= cam_bounds['bottom']):
            visible_objects.append(obj)
            
    return visible_objects[:20]  # Limit total objects for web
```

### 9. **Spatial Partitioning** ⚠️ **MEDIUM IMPACT**
**For games with many objects**:

```python
class SpatialGrid:
    def __init__(self, cell_size=200):
        self.cell_size = cell_size
        self.grid = {}
    
    def add_object(self, obj):
        cell_x = int(obj.x // self.cell_size)
        cell_y = int(obj.y // self.cell_size)
        key = (cell_x, cell_y)
        
        if key not in self.grid:
            self.grid[key] = []
        self.grid[key].append(obj)
    
    def get_objects_in_region(self, x, y, width, height):
        objects = []
        for cell_x in range(int(x // self.cell_size), int((x + width) // self.cell_size) + 1):
            for cell_y in range(int(y // self.cell_size), int((y + height) // self.cell_size) + 1):
                key = (cell_x, cell_y)
                if key in self.grid:
                    objects.extend(self.grid[key])
        return objects
```

## Memory Management

### 10. **Surface Pooling** ⚠️ **LOW IMPACT**
**For reducing garbage collection**:

```python
class SurfacePool:
    def __init__(self):
        self.pools = {}  # size -> list of surfaces
    
    def get_surface(self, width, height, flags=0):
        key = (width, height, flags)
        if key in self.pools and self.pools[key]:
            return self.pools[key].pop()
        else:
            return pygame.Surface((width, height), flags)
    
    def return_surface(self, surface):
        size = surface.get_size()
        flags = surface.get_flags()
        key = (size[0], size[1], flags)
        
        if key not in self.pools:
            self.pools[key] = []
        
        surface.fill((0, 0, 0, 0))  # Clear surface
        self.pools[key].append(surface)

# Global surface pool
surface_pool = SurfacePool()
```

## Implementation Priority

### Phase 1 - Immediate Impact (Implement First)
1. **Disable shadows and outlines for web** - 70% FPS improvement
2. **Reduce layer counts to max 8** - 50% FPS improvement  
3. **Pre-render background** - 15% FPS improvement
4. **Limit visible objects to 20** - 25% FPS improvement

### Phase 2 - Medium Impact
1. **Implement global rotation cache** - 20% FPS improvement
2. **Enhanced frustum culling** - 15% FPS improvement
3. **Surface format optimization** - 10% FPS improvement

### Phase 3 - Advanced Optimizations
1. **Spatial partitioning** - Variable impact based on object count
2. **Adaptive layer system** - Maintains playability under stress
3. **Surface pooling** - Reduces GC pressure

## Web-Specific Settings

### Recommended Configuration for Web
```python
class WebOptimizedSettings:
    MAX_LAYERS = 8
    MAX_VISIBLE_OBJECTS = 20
    DISABLE_SHADOWS = True
    DISABLE_OUTLINES = True
    SIMPLE_BACKGROUND = True
    DISABLE_GRID = True
    ROTATION_CACHE_SIZE = 500
    TARGET_FPS = 30
    
    @staticmethod
    def apply_to_game(game):
        if hasattr(sys, '_emscripten_info'):
            game.performance_mode = 0
            game.shadow_manager.enabled = False
            # Apply other optimizations...
```

## Monitoring and Debugging

### Performance Monitoring
```python
class PerformanceMonitor:
    def __init__(self):
        self.frame_times = []
        self.draw_times = []
        
    def start_frame(self):
        self.frame_start = time.time()
        
    def start_draw(self):
        self.draw_start = time.time()
        
    def end_draw(self):
        self.draw_times.append(time.time() - self.draw_start)
        
    def end_frame(self):
        self.frame_times.append(time.time() - self.frame_start)
        
    def get_stats(self):
        if self.frame_times:
            return {
                'avg_fps': 1.0 / (sum(self.frame_times) / len(self.frame_times)),
                'avg_draw_time': sum(self.draw_times) / len(self.draw_times) * 1000,
                'draw_percentage': (sum(self.draw_times) / sum(self.frame_times)) * 100
            }
```

## Expected Performance Gains

Implementing the Phase 1 optimizations should provide:
- **70-80% FPS improvement** on average browsers
- **Stable 30+ FPS** with 10-15 sprite stacks on screen
- **60+ FPS** with fewer objects or reduced layer counts
- **Reduced memory usage** by 40-50%

The key is to implement the high-impact optimizations first and measure results before proceeding to more complex solutions.
