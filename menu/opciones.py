"""Validación de las opciones que el cliente elige para un producto."""


def validar_seleccion(producto, ids):
    """Devuelve (opciones, texto, error).

    - opciones: lista de objetos Opcion elegidos, en el orden de los grupos.
    - texto: descripción para mostrar, por ejemplo "Proteína: Salmón".
    - error: mensaje si la selección no es válida (si no, cadena vacía).
    Solo cuentan las opciones disponibles del propio producto.
    """
    ids = set(ids)
    grupos = list(producto.grupos.prefetch_related('opciones'))
    todas = {o.pk for g in grupos for o in g.opciones.all() if o.disponible}
    if not ids.issubset(todas):
        return None, '', 'Una de las opciones elegidas ya no está disponible.'
    elegidas, partes = [], []
    for g in grupos:
        disponibles = [o for o in g.opciones.all() if o.disponible]
        propias = [o for o in disponibles if o.pk in ids]
        if g.obligatorio and disponibles and not propias:
            return None, '', f'Elige una opción en "{g.nombre}".'
        if len(propias) > g.max_selecciones:
            return None, '', (
                f'En "{g.nombre}" puedes elegir como máximo {g.max_selecciones}.')
        if propias:
            elegidas.extend(propias)
            partes.append(f'{g.nombre}: ' + ', '.join(o.nombre for o in propias))
    return elegidas, ' · '.join(partes)[:300], ''
