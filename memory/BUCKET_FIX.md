# Correção: Bucket Supabase Storage

## ❌ Problema
Geração automática de personagens falhava com erro:
```
{'statusCode': 404, 'error': Bucket not found, 'message': Bucket not found}
```

## 🔍 Causa Raiz
O Supabase Storage não tinha NENHUM bucket configurado. O código tentava fazer upload para bucket "pipeline-assets" que não existia.

## ✅ Solução
Criado bucket `pipeline-assets` programaticamente com permissões públicas:

```python
from supabase import create_client

supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
bucket = supabase.storage.create_bucket("pipeline-assets", options={"public": True})
```

## 📊 Resultado
- ✅ Bucket `pipeline-assets` criado com sucesso
- ✅ Imagens de personagens sendo geradas e salvas corretamente
- ✅ Upload funcionando (~18-20s por personagem)
- ✅ URLs públicas retornadas corretamente

## 🧪 Validação
Logs confirmam sucesso:
```
2026-03-29 18:57:34,435 - studiox - INFO - Successfully generated avatar for 'Casal de Coelhos'
2026-03-29 18:57:54,539 - studiox - INFO - Successfully generated avatar for 'Casal de Pássaros Azuis'
2026-03-29 18:58:25,858 - studiox - INFO - Successfully generated avatar for 'Casal de Raposas'
```

## 🔧 Arquivo Afetado
- `/app/backend/routers/studio/projects.py` (linha 417-422)
- Usa `supabase.storage.from_("pipeline-assets")` para upload

## 📝 Nota Importante
Se o Supabase for resetado ou o bucket deletado, será necessário recriar o bucket novamente usando o script acima.
