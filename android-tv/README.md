# OSAI OS TV - APK (Android TV / TV Box)

> **Aviso:** Este projeto foi feito com Vibe Coding (programação assistida por IA).
> Revise o código e teste antes de uso em produção.

App Android nativo (wrapper WebView) que abre a interface de TV do OSAI OS
(`/tv`) com suporte a Leanback launcher (aparece no launcher de Smart TV) e
controle remoto (D-pad).

## Estrutura

```
android-tv/
  settings.gradle
  build.gradle              (AGP 8.5.2, Kotlin 17)
  gradle.properties
  app/
    build.gradle            (minSdk 21, targetSdk 34)
    src/main/
      AndroidManifest.xml   LEANBACK_LAUNCHER + banner + cleartext (http na LAN)
      java/com/osai/tvbox/MainActivity.kt
      res/
        drawable/banner.png     (320x180)
        mipmap-*/ic_launcher.png (48..192)
        values/{strings,themes}.xml
```

O APK não contém lógica de negócio: toda a inteligência (dashboard, LLM,
pesquisa) vive no servidor `OSAI_tvbox.py` rodando no PC/Termux/container.
O APK só aponta a WebView para `http://SERVIDOR/tv`.

## Build

### Com Gradle instalado

```bash
cd android-tv
gradle assembleDebug
adb install -r app/build/outputs/apk/debug/app-debug.apk
```

### Com Android Studio

Abra a pasta `android-tv` (ele gera wrapper config) e depois
*Build > Build APK(s)*.

## Primeiro uso

1. No launcher da TV, abra **OSAI OS TV**.
2. Um diálogo pede o endereço do servidor, ex.: `http://192.168.1.105:8000`
   (sem `/tv` no final — o app adiciona).
3. Para trocar o endereço depois: tecla **MENU** do controle.
4. Sair do app: **VOLTAR** duas vezes (anti-saída acidental).

## Requisitos

- Servidor OSAI OS acessível na rede (`python OSAI_tvbox.py` no PC — ver
  `../README-TVBOX.md`) com a rota `/tv`.
- `android.permission.INTERNET` + `usesCleartextTraffic=true` já configurados
  para `http://` (LAN).

## Controles

| Tecla do controle | Ação |
|---|---|
| Setas (D-pad) | Navegar foco (a UI entrega navegação geométrica em JS) |
| OK / Enter | Ligar/desligar dispositivo, enviar mensagem, trocar aba |
| MENU | Reconfigurar endereço do servidor |
| VOLTAR | Voltar à tela "Casa" ou sair (dupla confirmação) |

## Alternativa sem APK

Instale o browser **TV Bro** na TV Box e use `http://IP-DO-SERVIDOR:8000/tv` — mesmo resultado, menos passos.
O APK existe para ter ícone próprio no launcher e configurar o IP uma única vez.
