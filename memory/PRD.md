# Adam (clone de adam-nn-demo)
- Clonado em 2026-11-21; Clerk gerenciado (app Adam); ElevenLabs via ELEVENLABS_API_KEY; torch 2.15.0 (CPU).
- 2026-11-22: voz ElevenLabs — plano gratuito usa vozes padrão; erros 502→400/500 (Cloudflare mascarava); torch sem +cpu e sem extra-index; .gitignore não bloqueia mais .env.
- 2026-11-22: Adam Desktop — programa local (backend/desktop: Iniciar-Adam.bat, iniciar.sh, adam_desktop.py) pareado por código de 6 dígitos; controla mouse/teclado/programas/terminal com permissão por ação, permissoes.json, adam_log.txt, parada de emergência; aba Extensões → Computador; rotas /api/desktop/*.
  Backlog: setup.exe (PyInstaller no Windows), OCR local, criptografia ponta a ponta além do HTTPS.
- 2026-11-22: AdamSetup.exe (NSIS + Python embutido, atalho na Área de Trabalho; build: backend/desktop_build/build_installer.sh; URL do servidor injetada no download); ferramenta de chat controlar_computador com cartão ao vivo; tela ao vivo; ações confiáveis por PC.
