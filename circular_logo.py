from PIL import Image, ImageDraw

img = Image.open('static/img/logo_foto.png').convert('RGBA')
blanco = Image.new('RGBA', img.size, (255, 255, 255, 255))
plano = Image.alpha_composite(blanco, img).convert('RGB')

# Caja del emblema: todo lo que no es casi blanco
caja = plano.convert('L').point(lambda v: 255 if v < 235 else 0).getbbox()
if caja is None:
    raise SystemExit('No encontré el emblema en la imagen.')
izq, arr, der, aba = caja
lado = max(der - izq, aba - arr)
cx, cy = (izq + der) // 2, (arr + aba) // 2
mitad = lado // 2

lienzo = Image.new('RGB', (lado, lado), (255, 255, 255))
lienzo.paste(plano, (mitad - cx, mitad - cy))

tam = 600
lienzo = lienzo.resize((tam, tam), Image.LANCZOS)
grande = tam * 4
margen = int(grande * 0.01)  # recorta un hilo del borde para que no quede halo blanco
mascara = Image.new('L', (grande, grande), 0)
ImageDraw.Draw(mascara).ellipse((margen, margen, grande - margen, grande - margen), fill=255)
salida = lienzo.convert('RGBA')
salida.putalpha(mascara.resize((tam, tam), Image.LANCZOS))
salida.save('static/img/logo_circular.png')
print('Listo: static/img/logo_circular.png')
