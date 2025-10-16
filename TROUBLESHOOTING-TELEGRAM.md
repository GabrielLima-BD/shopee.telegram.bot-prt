# 🚨 TROUBLESHOOTING - Vídeos não chegam no Telegram

## ✅ O que JÁ ESTÁ FUNCIONANDO:
- ✅ Bot está ATIVO (@ShopeeRecBot)
- ✅ Token configurado corretamente
- ✅ Chat ID configurado: `-1003111038846`
- ✅ Mensagem de TESTE foi enviada com sucesso

## ❌ PROBLEMA: Vídeos processados mas não chegam

### 🎯 CAUSA #1: Bot sem permissão no Canal (MAIS COMUM)

**Seu Chat ID é um CANAL**: `Videos Formatados ADM`

**SOLUÇÃO:**
1. Abra o Telegram
2. Vá para o canal `Videos Formatados ADM`
3. Clique no nome do canal (topo)
4. Vá em **Administradores**
5. Clique em **Adicionar Administrador**
6. Procure por `@ShopeeRecBot`
7. Adicione o bot como administrador
8. Dê as seguintes permissões:
   - ✅ Postar mensagens
   - ✅ Editar mensagens
   - ✅ Excluir mensagens

### 🎯 CAUSA #2: Vídeos muito grandes

**Limite do Telegram Bot API: 50 MB**

**SOLUÇÃO:**
- Vídeos > 50 MB **NÃO PODEM** ser enviados via Bot API
- Opções:
  1. Comprimir vídeo antes do upscale
  2. Usar bitrate menor no FFmpeg
  3. Usar resolução 720p ao invés de 1080p

### 🎯 CAUSA #3: Timeout no upload

**Upload pode demorar > 180 segundos**

**SOLUÇÃO:**
Já aumentei o timeout para 180s no código, mas se ainda falhar:
1. Verifique sua internet
2. Tente vídeos menores primeiro
3. Aumente timeout no código (linha 89 de `simple_processor.py`)

### 🎯 CAUSA #4: Codec incompatível

**Telegram aceita: H.264, H.265**

**SOLUÇÃO:**
O FFmpeg já converte automaticamente, mas se falhar:
1. Verifique logs do FFmpeg
2. Tente re-encodar manualmente

---

## 🧪 TESTES PARA FAZER:

### Teste 1: Verificar se mensagem de texto chega
```bash
python test_telegram.py
```
✅ Se chegou = Bot tem permissão
❌ Se não chegou = Bot SEM permissão no canal

### Teste 2: Enviar vídeo pequeno manualmente
1. Abra a GUI
2. Adicione UM vídeo pequeno (< 10 MB)
3. Processe
4. Veja os logs detalhados

### Teste 3: Verificar banco de dados
```bash
python check_videos.py
```

### Teste 4: Ver logs com mais detalhes
Agora os logs mostram:
- ✅ Tamanho do arquivo
- ✅ Status code da API
- ✅ Response do Telegram
- ✅ Message ID se enviado

---

## 📋 CHECKLIST DE VERIFICAÇÃO:

```
[ ] Bot está no canal como administrador?
[ ] Bot tem permissão para "Postar mensagens"?
[ ] Você é administrador do canal?
[ ] Vídeos são < 50 MB?
[ ] Internet está estável?
[ ] Logs mostram "✅ Enviado com sucesso"?
[ ] Você recebeu a mensagem de TESTE?
```

---

## 🔧 COMANDOS ÚTEIS:

### Ver todos os vídeos no banco:
```bash
sqlite3 data/videos_processados.db "SELECT id, status, error_message FROM videos_processados;"
```

### Limpar vídeos com falha:
```bash
sqlite3 data/videos_processados.db "DELETE FROM videos_processados WHERE status != 'processed';"
```

### Ver tamanho dos vídeos processados:
```bash
cd processed
dir
```

---

## 💡 SOLUÇÃO RÁPIDA:

**Se a mensagem de teste chegou mas os vídeos não:**

1. **GARANTIR que o bot é admin do canal:**
   - Telegram → Canal → Administradores → Adicionar `@ShopeeRecBot`

2. **Reprocessar os 20 vídeos:**
   - Abrir GUI
   - Clicar em "🔄 Reprocessar Falhas"
   - Acompanhar logs detalhados

3. **Verificar logs em tempo real:**
   - Olhe a janela de terminal/logs da GUI
   - Procure por `[SEND]` linhas
   - Verifique `Status Code: 200` e `Message ID`

---

## 📞 AINDA NÃO FUNCIONA?

Tire um print dos logs da GUI mostrando:
- `[SEND] Iniciando envio...`
- `[SEND] Status Code: XXX`
- `[SEND] Response: ...`

E me envie para diagnóstico mais detalhado!
