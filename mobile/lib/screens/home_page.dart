import 'package:flutter/material.dart';
import '../services/api_service.dart';
import '../services/auth_service.dart';
import '../models/estacion.dart';
import 'login_screen.dart';
import 'add_estacion.dart';
import 'dart:async';

class HomePage extends StatefulWidget {
  const HomePage({super.key});

  @override
  State<HomePage> createState() => _HomePageState();
}

class _HomePageState extends State<HomePage> {
  // Variable para guardar la lista de estaciones
  late Future<List<Estacion>> _futureEstaciones;
  Timer? _timer;

  @override
  void initState() {
    super.initState();
    _cargarEstaciones();
    _timer = Timer.periodic(const Duration(seconds: 3), (Timer t) {
    _cargarEstaciones();
    });
  }

  // Función que llama al ApiService para descargar los datos
  void _cargarEstaciones() {
    setState(() {
      _futureEstaciones = ApiService().fetchEstaciones();
    });
  }

  @override
  void dispose() {
    _timer?.cancel(); // Apaga el reloj
  super.dispose();
  }

  void _mostrarDialogoEdicion(Estacion estacion) {
    final nombreCtrl = TextEditingController(text: estacion.nombre);
    final ubicacionCtrl = TextEditingController(text: estacion.ubicacion);

    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text("Editar Estación"),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            TextField(controller: nombreCtrl, decoration: const InputDecoration(labelText: "Nombre")),
            TextField(controller: ubicacionCtrl, decoration: const InputDecoration(labelText: "Ubicación")),
          ],
        ),
        actions: [
          TextButton(onPressed: () => Navigator.pop(context), child: const Text("Cancelar")),
          ElevatedButton(
            onPressed: () async {
              bool ok = await ApiService().editarEstacion(estacion.id, nombreCtrl.text, ubicacionCtrl.text);
              if (ok) {
                if (!context.mounted) return;
                Navigator.pop(context); // Cierra la ventana emergente
                _cargarEstaciones(); // Vuelve a descargar los datos actualizados
              }
            },
            child: const Text("Guardar"),
          )
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Estaciones SMAT'),
        actions: [
          IconButton(
            icon: const Icon(Icons.logout),
            onPressed: () async {
              // Borramos el token de la memoria
              await AuthService().logout();
              
              if (!context.mounted) return;

              // Reinicia la pagina y devuelve a la pagina de inicio de sesion
              Navigator.pushAndRemoveUntil(
                context,
                MaterialPageRoute(builder: (context) => const LoginScreen()),
                (route) => false,
              );
            },
          ),
        ],
      ),


      // FutureBuilder para mostrar una bolita de carga mientras llegan los datos
      body: RefreshIndicator(
        onRefresh: () async {
          _cargarEstaciones();
        },
        child: FutureBuilder<List<Estacion>>(
          future: _futureEstaciones,
          builder: (context, snapshot) {
            if (snapshot.connectionState == ConnectionState.waiting) {
              return const Center(child: CircularProgressIndicator());
            } else if (snapshot.hasError) {
              return Center(child: Text('Error al cargar datos: ${snapshot.error}'));
            } else if (!snapshot.hasData || snapshot.data!.isEmpty) {
              return const Center(child: Text('No hay estaciones registradas aún.'));
            }
        
            final estaciones = snapshot.data!;
            return ListView.builder(
              physics: const AlwaysScrollableScrollPhysics(),
              itemCount: estaciones.length,
              itemBuilder: (context, index) {
                final estacion = estaciones[index];

                //Reto del Color

                Color colorDelSensor = Colors.blue;
                if (estacion.ultimoValor != null) {
                  if (estacion.ultimoValor! > 70) {
                    colorDelSensor = Colors.red;
                  } else {
                    colorDelSensor = Colors.green;
                  }
                }
        
                //
                
                return Dismissible(
                  key: Key(estacion.id.toString()),
                  direction: DismissDirection.endToStart,
                  background: Container(
                    color: Colors.red,
                    alignment: Alignment.centerRight,
                    padding: const EdgeInsets.only(right: 20),
                    child: const Icon(Icons.delete, color: Colors.white),
                  ),
                  onDismissed: (direction) async {
                    // Usamos ApiService() con mayúscula
                    bool ok = await ApiService().eliminarEstacion(estacion.id);
                    if (ok) {
                      // Refrescamos la lista si se borró con éxito
                      _cargarEstaciones();
                      
                      if (!context.mounted) return;
                      ScaffoldMessenger.of(context).showSnackBar(
                        SnackBar(content: Text("${estacion.nombre} eliminada")),
                      );
                    }
                  },
                  child: ListTile(
                    leading: Icon(Icons.sensors, color: colorDelSensor),
                    title: Text(estacion.nombre),
                    subtitle: Text(estacion.ubicacion),
                    trailing: estacion.ultimoValor != null
                        ? Text(
                            "${estacion.ultimoValor!.toStringAsFixed(1)} cm",
                            style: TextStyle(
                              fontSize: 16,
                              fontWeight: FontWeight.bold,
                              color: colorDelSensor, // Mantiene el color del reto
                            ),
                          )
                        : const Text("Sin datos"),
                    onTap: () => _mostrarDialogoEdicion(estacion), // Siguiente paso
                  ),
                );
              },
            );
          },
        ),
      ),
      // Botón flotante para ir a la pantalla de crear una nueva estación
      floatingActionButton: FloatingActionButton(
        onPressed: () async {
          final result = await Navigator.push(
            context,
            MaterialPageRoute(builder: (context) => const AddEstacionScreen()),
          );
          
          // Si el usuario guardó con éxito (result == true), recargamos la lista
          if (result == true) {
            _cargarEstaciones();
          }
        },
        child: const Icon(Icons.add),
      ),
    );
  }
}