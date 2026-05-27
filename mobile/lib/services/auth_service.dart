import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';
class AuthService {

  //El url puede ser editado a localhost. Solo fue cambiado por temas de conexión.
  final String baseUrl = "https://tying-backtrack-subprime.ngrok-free.dev";
  Future<bool> login(String username, String password) async {
    // Nota: El endpoint /token suele esperar un form-data, pero por simplicidad
    // en este lab usaremos un POST simple según el backend construido.
    final response = await http.post(Uri.parse('$baseUrl/token'));
    if (response.statusCode == 200) {
      final data = jsonDecode(response.body);
      final String token = data['access_token'];
      // Guardar token en el almacenamiento del teléfono
      final prefs = await SharedPreferences.getInstance();
      await prefs.setString('jwt_token', token);
      return true;
    }
    return false;
  }

  Future<String?> getToken() async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getString('jwt_token');
  }
  Future<void> logout() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove('jwt_token');
  }
}