# IceFlix
Author: Iago García Suárez
Github: https://github.com/IagoGarciaSuarez/IceFlix_SSDD

# Template project for ssdd-lab

This repository is a Python project template. It contains the
following files and directories:

- `packagename` is the main Python package. You should rename it to
  something meaninful for your project.
- `packagename/__init__.py` is an empty file needed by Python to
  recognise the `packagename` directory as a Python package/module.
- `packagename/cli.py` contains several functions that can handle the
  basic console entry points defined in `python.cfg`. The name of the
  submodule and the functions can be modified if you need.
- `pyproject.toml` defines the build system used in the project.
- `run_client` should be a script that can be run directly from the
  repository root directory. It should be able to run the IceFlix
  client.
- `run_iceflix` should be a script that can be run directly from the
  repository root directory. It should be able to run all the services
  in background in order to test the whole system.
- `setup.cfg` is a Python distribution configuration file for
  Setuptools. It needs to be modified in order to adeccuate to the
  package name and console handler functions.


## Project description

This project will recreate the way Netflix works from a distributed systems 
developer perspective.
Using Zeroc-ice, a small emulation of a video streaming service will be built.

## Instrucciones de ejemplo de uso

Para utilizar IceFlix se deberán llevar a cabo los siguientes pasos.
1. Ejecutar run_iceflix.
  - >./run_iceflix
2. Ejecutar, en otra terminal, run_client con ./run_client
  - >./run_client
3. Una vez iniciado el cliente de IceFlix se deberá indicar el proxy del servicio 
main de IceFlix al que debe conectarse. El proxy puede estar indicado entre 
comillas, dobles o simples, o sin comillas. Se puede hacer con:
  - >iniciar MainService -t -e 1.1:tcp -h 172.19.148.8 -p 7070 -t 60000
4. Si se ha realizado correctamente, ya se podrán utilizar las funcionalidades de 
IceFlix. Para seleccionar un medio se deberá iniciar sesión como administrador, si
se dispone de un token de administrador válido, o como usuario, si tenemos una cuenta.
El token de administrador es 'sysadmin' y la cuenta de usuario normal es 'iago' con 
contraseña 'mipass'. Elegiremos por lo tanto una de las siguientes opciones:
  - Como admin:
      >adminlogin
      
      >Token de administrador: sysadmin
  - Como usuario:
      >login
      
      >Nombre de usuario: iago
      
      >Contraseña: mipass
5. Una vez se haya iniciado sesión debemos seleccionar un medio para cambiarle 
el nombre o las tags o para reproducirlo. Para ello necesitaremos el id del medio,
que podremos encontrar al realizar una búsqueda. En este repositorio se dispone
de un único medio para realizar las pruebas, que se llama "Perro cachorro.mp4".
El comando de búsqueda tiene 4 distintas variantes según el modo de búsqueda deseado.
Podemos ver la descripción de cada una escribiendo
  - >help search

  Para este caso, utilizaremos la búsqueda por nombre no exacto:
  - >search 2 Perro
6. Deberíamos obtener la información del medio, entre la que se ve el ID. La búsqueda
por nombre (opciones 1 y 2) se puede realizar sin iniciar sesión, pero los siguientes
pasos requerirán una sesión de usuario o de administrador. Lo copiamos y escribimos 
el siguiente comando para seleccionarlo:
  - >select 8f079e802a8340f4b458bd4d9dd3847568b58752c7672ed23b96e6a22cdb6103
7. Para reproducirlo escribiremos el siguiente comando:
  - >play
8. Para pararlo es importante que NO se cierre la ventana manualmente, sino que se
deberá escribir el comando:
  - >stop
9. Si queremos cambiarle el nombre deberemos estar loggeados como administrador. En
caso de que se haya iniciado una sesión de usuario podremos cerrarla escribiendo:
  - >logout

Una vez seamos administradores y volvamos a tener el medio seleccionado, podremos 
renombrar el medio por ejemplo, a Perro pequeño, escribiendo:
  - >rename Perro pequeño
10. Si queremos editar sus tags deberemos estar loggeados como un usuario normal.
Es importante recordar que las tags son sensibles a mayúsculas y minúsculas.
Con el medio seleccionado, tendremos dos opciones según lo que queramos hacer:
  - Añadir nuevas tags. Añadiremos las tags "Gracioso" y "Relax":
    > addtags Gracioso, Relax
  - Eliminar tags. Eliminaremos la tag "Relax" añadida previamente:
    > removetags Relax

Para cerrar el cliente puede utilizar el comando 
  - >q

Para más comandos, el comando "help" mostrará todos los comandos disponibles, y con
"help \<comando\>" se mostrará una descripción más detallada sobre el comando indicado.

 
