def mochila_tabla(pedidos: list, capacidad_kg: float) -> dict:
    factor = 10
    W = int(round(capacidad_kg * factor))
    n = len(pedidos)

    dp = [[0.0] * (W + 1) for _ in range(n + 1)]

    for i in range(1, n + 1):
        peso_u = int(round(pedidos[i - 1].peso * factor))   
        valor  = pedidos[i - 1].valor                        

        for w in range(W + 1):
            dp[i][w] = dp[i - 1][w]
            if peso_u <= w:
                con_item = dp[i - 1][w - peso_u] + valor
                if con_item > dp[i][w]:
                    dp[i][w] = con_item
    seleccionados = []
    w = W
    for i in range(n, 0, -1):
        if dp[i][w] != dp[i - 1][w]:      
            seleccionados.append(pedidos[i - 1])
            w -= int(round(pedidos[i - 1].peso * factor))
    seleccionados.reverse()

    peso_total   = sum(p.peso  for p in seleccionados)
    valor_maximo = dp[n][W]

    return {
        "valor_maximo": valor_maximo,
        "pedidos_sel":  seleccionados,
        "peso_total":   round(peso_total, 2),
        "tabla_dp":     dp,
        "n_pedidos":    n,
        "capacidad_W":  W,
        "factor":       factor
    }


def mochila_optimizado(pedidos: list, capacidad_kg: float) -> dict:
    factor = 10
    W  = int(round(capacidad_kg * factor))
    dp = [0.0] * (W + 1)

    for pedido in pedidos:
        peso_u = int(round(pedido.peso  * factor))
        valor  = pedido.valor
        for w in range(W, peso_u - 1, -1):
            dp[w] = max(dp[w], dp[w - peso_u] + valor)

    return {"valor_maximo": dp[W]}


def analizar_carga_repartidor(repartidor, pedidos_candidatos: list) -> dict:
    return mochila_tabla(pedidos_candidatos, repartidor.capacidad_kg)