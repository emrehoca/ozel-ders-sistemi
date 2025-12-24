import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';

void main() => runApp(OzelDersApp());

class OzelDersApp extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Özel Ders Sistemi',
      home: LoginScreen(),
    );
  }
}

class LoginScreen extends StatefulWidget {
  @override
  _LoginScreenState createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen> {
  final _username = TextEditingController();
  final _password = TextEditingController();

  Future<void> _login() async {
    // Gerçek hosting URL'sini buraya yaz
    final response = await http.post(Uri.parse('http://localhost:5000/login'), body: {
      'username': _username.text,
      'password': _password.text,
    });
    if (response.statusCode == 200) {
      Navigator.pushReplacement(context, MaterialPageRoute(builder: (_) => AnaSayfa()));
    } else {
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Giriş başarısız')));
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text('Giriş Yap')),
      body: Padding(
        padding: EdgeInsets.all(20),
        child: Column(
          children: [
            TextField(controller: _username, decoration: InputDecoration(label: 'Kullanıcı Adı')),
            TextField(controller: _password, decoration: InputDecoration(label: 'Şifre'), obscureText: true),
            ElevatedButton(onPressed: _login, child: Text('Giriş Yap')),
          ],
        ),
      ),
    );
  }
}

class AnaSayfa extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text('Özel Ders Sistemi')),
      body: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            ElevatedButton(onPressed: () {}, child: Text('Öğrenciler')),
            ElevatedButton(onPressed: () {}, child: Text('Dersler')),
            ElevatedButton(onPressed: () {}, child: Text('Ödevler')),
            ElevatedButton(onPressed: () {}, child: Text('Takvim')),
            ElevatedButton(onPressed: () {}, child: Text('Ödemeler')),
          ],
        ),
      ),
    );
  }
}