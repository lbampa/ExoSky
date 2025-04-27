import pygame
import numpy as np
import pandas as pd

from exosky.data import read_data
from exosky.projections import project
from astropy.coordinates import SkyCoord

constellation_colors = {
    'Ursa Major': (0, 255, 255),
    'Orion': (255, 0, 0),
    'Scorpius   ': (0, 255, 0),
}

def generate_star_color(magnitude, constellation):
    # distance = float(d)
    # r = min(255, 255 * 1/(distance*100)**2)
    # g = min(255, 240 * 1/(distance*100)**2)
    # b = min(255, 255 * 1/(distance*100)**2)
    # this should return white star multiplied by a factor
    # depending on the magnitude of the star
    # 0 is the brightest magnitude
    # 5 is the limit of the naked eye
    # this is a logarithmic scale
    base = 2
    bright = base ** (4 -magnitude * 2)
    bright *= 2
    r_color, g_color, b_color = constellation_colors.get(constellation, (255, 255, 255))

    
    # r = max(min(int(r_color * bright), r_color), 0)
    # g = max(min(int(g_color * bright), g_color), 0)
    # b = max(min(int(b_color * bright), b_color), 0)
    # return (r, g, b)
    return (r_color, g_color, b_color)

def load_data():
    #df = pd.read_csv('data/stars_around_Proxima_Cen_b.csv')
    #df = pd.read_csv('data/stars_around_Proxima_Cen_b.csv')
    #df = pd.read_csv('tests/full_bright_stars_catalog.csv')
    df = read_data("tests/official_constellation_figure_stars.csv")
    # the columns x, y, z should make an np.array of shape (n, 3)
    # sort by distance
    # df = df.sort_values(by="distance")
    # filter first 1000
    # create a field with the SkyCoord object in cartesian coordinates from xyz
    #df["coords"] = df.apply(lambda x: SkyCoord(x["x"], x["y"], x["z"], unit="pc", representation_type="cartesian"), axis=1) 
    #filter first 1000
    #df = df.head(1000)
    #df["constellation"] = df["coords"].apply(lambda x: x.get_constellation())
    #df.to_csv('sun_surroundings3_constellations.csv', index=False)
    #df = df[df["constellation"] == 'Ursa Major']
    # print(df.head())

    # print(min(df["x"]))
    # print(max(df["x"]))
    # print(min(df["y"]))
    # print(max(df["y"]))
    # print(min(df["z"]))
    # print(max(df["z"]))

    #df = df.head(8)
    # get the x, y, z columns and convert them to a SkyCoord object

    df["array"] = df.apply(lambda x: np.array([x["x"], x["y"], x["z"]]), axis=1)
    coords = np.array(df["array"].to_list())
    return coords, np.array(df["mag"].to_list()), np.array(df["constellation"].to_list())

def main():
    pygame.init()
    dragging = False
    SCREEN_WIDTH = 1920
    SCREEN_HEIGHT = 1080

    FOV = 720  # Campo de visión de la cámara
    CAMERA_DISTANCE = 0.0000001  # Distancia de la cámara al centro

    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    clock = pygame.time.Clock()
    
    sphere_points, magnitudes, constellations = load_data()
    rotated_points = sphere_points.copy()
    angle_x = angle_y = angle_z = 0
    camera_position = np.array([0, 0, -CAMERA_DISTANCE])
    zoom = 1  # El observador está dentro de la esfera

    pressed_keys = {}

    while True:
        screen.fill((0, 0, 0))  # Limpiar la pantalla en cada frame
        clock.tick(60)

        rotated_points = project(rotated_points, angle_x, angle_y, angle_z, zoom)
        rotated_points -= camera_position
        camera_position = np.array([0, 0, 0])
        angle_x = angle_y = angle_z = 0
        # Aplicar rotación a cada punto de la esfera
        for projected_point, magnitude, constellation in zip(rotated_points, magnitudes, constellations):
            if projected_point[2] < 0:  # Solo mostrar estrellas delante del observador
                continue
            scale = FOV / projected_point[2]  # Factor de escala basado en la distancia
            
            x = int(projected_point[0] * scale) + SCREEN_WIDTH // 2  # Centrar en la pantalla
            y = int(-projected_point[1] * scale) + SCREEN_HEIGHT // 2  # Invertir Y y centrar

            # Cambiar tamaño según la distancia (coordenada Z)
            distance_factor = 10 / (1 + projected_point.dot(projected_point))**2
            #distance_factor = 0.002 / projected_point.dot(projected_point)

            # make distance_factor 
            distance_factor = max(0.2, distance_factor)

            
            point_size = int(0.2 * distance_factor)  # Tamaño según distancia
            point_size = 1

            # Generar color de la estrella basado en la distancia
            star_color = generate_star_color(magnitude, constellation)

            # Dibujar el punto con su color y tamaño
            pygame.draw.circle(screen, star_color, (x, y), point_size)

        pygame.draw.circle(screen, (255, 255, 200), (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2), 10)  # Dibujar el Sol

        # Manejo de eventos de Pygame
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()  # Salir correctamente
            
            # Iniciar el arrastre con el clic del ratón
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Si el botón izquierdo del ratón está presionado
                    dragging = True
                    last_mouse_pos = pygame.mouse.get_pos()

            # Terminar el arrastre al soltar el botón del ratón
            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1:
                    dragging = False

            # Actualizar la rotación durante el arrastre
            elif event.type == pygame.MOUSEMOTION and dragging:
                mouse_x, mouse_y = pygame.mouse.get_pos()

                # Calcular la diferencia de posición del ratón
                dx = mouse_x - last_mouse_pos[0]
                dy = mouse_y - last_mouse_pos[1]

                # Ajustar los ángulos de rotación basados en el movimiento del ratón
                angle_y -= np.radians(dx) * 0.1  # Rotar alrededor del eje Y (horizontalmente)
                angle_x -= np.radians(dy) * 0.1  # Rotar alrededor del eje X (verticalmente)

                last_mouse_pos = (mouse_x, mouse_y)  # Actualizar la última posición del ratón

            elif event.type == pygame.KEYDOWN:
                pressed_keys[event.key] = True
            elif event.type == pygame.KEYUP:
                pressed_keys[event.key] = False

            for key, pressed in pressed_keys.items():
                if not pressed:
                    continue
                if key == pygame.K_ESCAPE:
                    pygame.quit()
                    exit()
                elif key == pygame.K_r:
                    # Resetear la rotación
                    angle_x = angle_y = angle_z = 0
                    # resetear la posición de la cámara
                    camera_position = np.array([0, 0, -CAMERA_DISTANCE])
                    # resetear el zoom
                    zoom = 1
                    # resetear el FOV
                    FOV = 720
                elif key == pygame.K_q:
                    # hacer roll
                    angle_z += 0.1
                elif key == pygame.K_e:
                    # hacer roll
                    angle_z -= 0.1
                elif key == pygame.K_w:
                    # mirar hacia arriba
                    angle_x += 0.1
                elif key == pygame.K_s:
                    # mirar hacia abajo
                    angle_x -= 0.1
                elif key == pygame.K_a:
                    # mirar hacia la izquierda
                    angle_y += 0.1
                elif key == pygame.K_d:
                    # mirar hacia la derecha
                    angle_y -= 0.1

        pygame.display.update()

if __name__ == "__main__":
    main()
