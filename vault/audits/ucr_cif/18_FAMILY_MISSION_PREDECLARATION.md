---
title: UCR-CIF -- S1: predeclaracion de los sujetos del clasificador de familia, ANTES de escribirlo
date: 2026-09-24
status: PREDECLARADO -- se commitea SOLO, antes de vault/tower/families/ y de su clasificador
spec: docs/superpowers/specs/2026-09-24-family-baselines-design.md §4
binding: si el clasificador contradice esto, gana la medicion y se registra; no se cambia de sujeto
---

# S1 -- sujetos del clasificador, nombrados antes

## 1. Por prompt (lo que decide la inyeccion)

| familia | DENTRO (debe clasificar) | FUERA (no debe) |
|---|---|---|
| `web_surface` | «hazme una landing para un restaurante con reservas online» | «arregla el crash del escritor de level.dat en la Wii» |
| `kobiicraft_mode` | «crea una nueva modalidad de KobiiCraft tipo skywars con arenas y kits» | «hazme una landing para un restaurante con reservas online» |
| `persistent_state` | «anade una tabla de suscripciones con su migracion al backend de InfinityOps» | «cambia el color del boton del hero» |
| `wii_homebrew` | «porta el menu de CavEX a la Wii con libogc y GX» | «crea una nueva modalidad de KobiiCraft tipo skywars con arenas y kits» |

**Control positivo global:** «que hora es» no clasifica en NINGUNA familia.

**Caso duro, declarado para que pueda fallar:** «haz una landing para anunciar la nueva modalidad
de KobiiCraft» -> esperado `web_surface` DENTRO y `kobiicraft_mode` FUERA: se construye una web,
no una modalidad. Si el clasificador mete las dos, se registra como sobre-emparejamiento y NO se
ajusta hasta despues de registrarlo.

## 2. Por repo (lo que decide a que familia promociona un deposito)

| familia | DENTRO | FUERA |
|---|---|---|
| `web_surface` | `CostaLuz Lawyers` | `CavEX` |
| `kobiicraft_mode` | `KobiiCraft Core Files` | `CostaLuz Lawyers` |
| `persistent_state` | `InfinityOps` | `ABSW2-Wii` (vinculante desde P2, commit 3b3ae85) |
| `wii_homebrew` | `CavEX` | `InfinityOps` |

## 3. Que cuenta como fallo

- Cualquier DENTRO fuera, o FUERA dentro -> fallo de la senal, registrado.
- «que hora es» en alguna familia -> falsa activacion, STOP.
- Un sujeto de repo que no existe en disco -> resultado INVALIDO, no negativo.
