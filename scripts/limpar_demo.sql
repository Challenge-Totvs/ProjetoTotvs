-- =====================================================================================================
-- limpar_demo.sql (Oracle 12c ou superior)
--
-- OBJETIVO
--   Apagar os dados criados pelos testes e ensaios (reuniões, transcrições, análises, temas, citações,
--   eventos de tema, compromissos e notificações), para que o hash de transcrição duplicada
--   (409 transcricao_duplicada) não bloqueie a demo. Usuários (CONSULTOR), clientes (CLIENTE), contatos
--   (CONTATO) e o catálogo de padrões (PADRAO) NÃO são tocados.
--
-- ANTES DE RODAR
--   1. Faça BACKUP do schema (ex.: expdp ou export pelo SQL Developer).
--   2. Rode só DEPOIS do último ensaio, com o backend parado.
--   3. Rode a seção 1 (CONFERÊNCIA) e confira os números antes da seção 2.
--
-- COMO SEPARA SEED DE TESTE
--   O CargaDemo grava o seed (src/main/resources/demo/seed.json) uma única vez, num banco vazio, antes de
--   qualquer teste, e ele só roda de novo se a conta-marca não existir. Como os ids são IDENTITY
--   crescentes, os N primeiros ids de cada tabela são do seed; o que vier depois é teste. N vem do
--   seed.json atual:
--     REUNIAO 33 · TRANSCRICAO 27 · ANALISE 27 · TEMA 47 · CITACAO 60 · EVENTO_TEMA 1 · COMPROMISSO 8
--     NOTIFICACAO 0 (o seed não grava notificação: todas são de teste)
--   Se o seed.json mudar, atualize esses números aqui. Se faltar linha do seed numa tabela, o corte cai
--   no maior id existente e nada dessa tabela é apagado (erro para o lado seguro).
-- =====================================================================================================


-- =====================================================================================================
-- 1. CONFERÊNCIA (só leitura)
-- =====================================================================================================

-- 1.1 Total por tabela afetada
SELECT 'REUNIAO'     AS tabela, COUNT(*) AS total FROM REUNIAO
UNION ALL SELECT 'TRANSCRICAO', COUNT(*) FROM TRANSCRICAO
UNION ALL SELECT 'ANALISE',     COUNT(*) FROM ANALISE
UNION ALL SELECT 'TEMA',        COUNT(*) FROM TEMA
UNION ALL SELECT 'CITACAO',     COUNT(*) FROM CITACAO
UNION ALL SELECT 'EVENTO_TEMA', COUNT(*) FROM EVENTO_TEMA
UNION ALL SELECT 'COMPROMISSO', COUNT(*) FROM COMPROMISSO
UNION ALL SELECT 'NOTIFICACAO', COUNT(*) FROM NOTIFICACAO;

-- 1.2 Quanto sairia de cada tabela (mesmos critérios da seção 2)
SELECT 'REUNIAO' AS tabela, COUNT(*) AS a_apagar FROM REUNIAO
 WHERE id > (SELECT NVL(MAX(id), 0) FROM (SELECT id FROM REUNIAO ORDER BY id FETCH FIRST 33 ROWS ONLY))
UNION ALL
SELECT 'TRANSCRICAO', COUNT(*) FROM TRANSCRICAO
 WHERE id > (SELECT NVL(MAX(id), 0) FROM (SELECT id FROM TRANSCRICAO ORDER BY id FETCH FIRST 27 ROWS ONLY))
    OR reuniao_id > (SELECT NVL(MAX(id), 0) FROM (SELECT id FROM REUNIAO ORDER BY id FETCH FIRST 33 ROWS ONLY))
UNION ALL
SELECT 'ANALISE', COUNT(*) FROM ANALISE
 WHERE id > (SELECT NVL(MAX(id), 0) FROM (SELECT id FROM ANALISE ORDER BY id FETCH FIRST 27 ROWS ONLY))
    OR transcricao_id > (SELECT NVL(MAX(id), 0) FROM (SELECT id FROM TRANSCRICAO ORDER BY id FETCH FIRST 27 ROWS ONLY))
UNION ALL
SELECT 'TEMA', COUNT(*) FROM TEMA
 WHERE id > (SELECT NVL(MAX(id), 0) FROM (SELECT id FROM TEMA ORDER BY id FETCH FIRST 47 ROWS ONLY))
UNION ALL
SELECT 'CITACAO', COUNT(*) FROM CITACAO
 WHERE id > (SELECT NVL(MAX(id), 0) FROM (SELECT id FROM CITACAO ORDER BY id FETCH FIRST 60 ROWS ONLY))
    OR tema_id > (SELECT NVL(MAX(id), 0) FROM (SELECT id FROM TEMA ORDER BY id FETCH FIRST 47 ROWS ONLY))
    OR reuniao_id > (SELECT NVL(MAX(id), 0) FROM (SELECT id FROM REUNIAO ORDER BY id FETCH FIRST 33 ROWS ONLY))
UNION ALL
SELECT 'EVENTO_TEMA', COUNT(*) FROM EVENTO_TEMA
 WHERE id > (SELECT NVL(MAX(id), 0) FROM (SELECT id FROM EVENTO_TEMA ORDER BY id FETCH FIRST 1 ROWS ONLY))
    OR tema_id > (SELECT NVL(MAX(id), 0) FROM (SELECT id FROM TEMA ORDER BY id FETCH FIRST 47 ROWS ONLY))
UNION ALL
SELECT 'COMPROMISSO', COUNT(*) FROM COMPROMISSO
 WHERE id > (SELECT NVL(MAX(id), 0) FROM (SELECT id FROM COMPROMISSO ORDER BY id FETCH FIRST 8 ROWS ONLY))
    OR reuniao_id > (SELECT NVL(MAX(id), 0) FROM (SELECT id FROM REUNIAO ORDER BY id FETCH FIRST 33 ROWS ONLY))
UNION ALL
SELECT 'NOTIFICACAO', COUNT(*) FROM NOTIFICACAO;

-- 1.3 Cadastros que devem continuar iguais depois da limpeza (anote os números)
SELECT 'CONSULTOR' AS tabela, COUNT(*) AS total FROM CONSULTOR
UNION ALL SELECT 'CLIENTE', COUNT(*) FROM CLIENTE
UNION ALL SELECT 'CONTATO', COUNT(*) FROM CONTATO
UNION ALL SELECT 'PADRAO',  COUNT(*) FROM PADRAO;


-- =====================================================================================================
-- 2. LIMPEZA (uma transação; termina em ROLLBACK por padrão)
--    Ordem: filhas antes das mães. Nada aqui apaga CONSULTOR, CLIENTE, CONTATO ou PADRAO.
-- =====================================================================================================

-- No Oracle a transação começa sozinha no primeiro DELETE. Confirme que o AUTOCOMMIT está DESLIGADO
-- (SQL*Plus: SET AUTOCOMMIT OFF; SQL Developer: Preferências > Banco de Dados > Avançado), senão o
-- ROLLBACK do fim não desfaz nada.

-- 2.1 NOTIFICACAO (FK tema_id -> TEMA). O seed não grava notificação: todas vieram de teste.
DELETE FROM NOTIFICACAO;

-- 2.2 EVENTO_TEMA (FK tema_id -> TEMA): eventos de teste e todos os eventos de temas de teste.
DELETE FROM EVENTO_TEMA
 WHERE id > (SELECT NVL(MAX(id), 0) FROM (SELECT id FROM EVENTO_TEMA ORDER BY id FETCH FIRST 1 ROWS ONLY))
    OR tema_id > (SELECT NVL(MAX(id), 0) FROM (SELECT id FROM TEMA ORDER BY id FETCH FIRST 47 ROWS ONLY));

-- 2.3 CITACAO (FK tema_id -> TEMA, reuniao_id -> REUNIAO): inclui citações de teste presas a temas do seed.
DELETE FROM CITACAO
 WHERE id > (SELECT NVL(MAX(id), 0) FROM (SELECT id FROM CITACAO ORDER BY id FETCH FIRST 60 ROWS ONLY))
    OR tema_id > (SELECT NVL(MAX(id), 0) FROM (SELECT id FROM TEMA ORDER BY id FETCH FIRST 47 ROWS ONLY))
    OR reuniao_id > (SELECT NVL(MAX(id), 0) FROM (SELECT id FROM REUNIAO ORDER BY id FETCH FIRST 33 ROWS ONLY));

-- 2.4 COMPROMISSO (FK reuniao_id -> REUNIAO).
DELETE FROM COMPROMISSO
 WHERE id > (SELECT NVL(MAX(id), 0) FROM (SELECT id FROM COMPROMISSO ORDER BY id FETCH FIRST 8 ROWS ONLY))
    OR reuniao_id > (SELECT NVL(MAX(id), 0) FROM (SELECT id FROM REUNIAO ORDER BY id FETCH FIRST 33 ROWS ONLY));

-- 2.5 ANALISE (FK transcricao_id -> TRANSCRICAO).
DELETE FROM ANALISE
 WHERE id > (SELECT NVL(MAX(id), 0) FROM (SELECT id FROM ANALISE ORDER BY id FETCH FIRST 27 ROWS ONLY))
    OR transcricao_id > (SELECT NVL(MAX(id), 0) FROM (SELECT id FROM TRANSCRICAO ORDER BY id FETCH FIRST 27 ROWS ONLY));

-- 2.6 TRANSCRICAO (FK reuniao_id -> REUNIAO). Aqui sai o hash_texto que gera o 409; inclui transcrições
--     de teste enviadas para reuniões agendadas do seed.
DELETE FROM TRANSCRICAO
 WHERE id > (SELECT NVL(MAX(id), 0) FROM (SELECT id FROM TRANSCRICAO ORDER BY id FETCH FIRST 27 ROWS ONLY))
    OR reuniao_id > (SELECT NVL(MAX(id), 0) FROM (SELECT id FROM REUNIAO ORDER BY id FETCH FIRST 33 ROWS ONLY));

-- 2.7 TEMA: zera as auto-referências que apontam para temas de teste antes de apagá-los.
--     semelhante_nao_procede_id não tem FK no JPA, mas é zerado para não sobrar id solto.
UPDATE TEMA SET semelhante_nao_procede_id = NULL
 WHERE semelhante_nao_procede_id IS NOT NULL
   AND (id > (SELECT NVL(MAX(id), 0) FROM (SELECT id FROM TEMA ORDER BY id FETCH FIRST 47 ROWS ONLY))
        OR semelhante_nao_procede_id > (SELECT NVL(MAX(id), 0) FROM (SELECT id FROM TEMA ORDER BY id FETCH FIRST 47 ROWS ONLY)));

UPDATE TEMA SET anterior_id = NULL
 WHERE anterior_id > (SELECT NVL(MAX(id), 0) FROM (SELECT id FROM TEMA ORDER BY id FETCH FIRST 47 ROWS ONLY));

DELETE FROM TEMA
 WHERE id > (SELECT NVL(MAX(id), 0) FROM (SELECT id FROM TEMA ORDER BY id FETCH FIRST 47 ROWS ONLY));

-- 2.8 REUNIAO: por último, porque TRANSCRICAO, CITACAO e COMPROMISSO apontam para ela.
DELETE FROM REUNIAO
 WHERE id > (SELECT NVL(MAX(id), 0) FROM (SELECT id FROM REUNIAO ORDER BY id FETCH FIRST 33 ROWS ONLY));

-- 2.9 Devolve o status do seed às reuniões do seed que ficaram sem transcrição (receberam uma de teste e
--     viraram ANALISADA). No seed são 6: a de data mais antiga é a "aguardando" (REALIZADA); as outras
--     5 são AGENDADA.
UPDATE REUNIAO r
   SET r.status = CASE
                    WHEN r.data_hora = (SELECT MIN(r2.data_hora) FROM REUNIAO r2
                                         WHERE r2.id <= (SELECT NVL(MAX(id), 0) FROM (SELECT id FROM REUNIAO ORDER BY id FETCH FIRST 33 ROWS ONLY))
                                           AND NOT EXISTS (SELECT 1 FROM TRANSCRICAO t2 WHERE t2.reuniao_id = r2.id))
                    THEN 'REALIZADA'
                    ELSE 'AGENDADA'
                  END
 WHERE r.id <= (SELECT NVL(MAX(id), 0) FROM (SELECT id FROM REUNIAO ORDER BY id FETCH FIRST 33 ROWS ONLY))
   AND NOT EXISTS (SELECT 1 FROM TRANSCRICAO t WHERE t.reuniao_id = r.id);

-- 2.10 Confira de novo (dentro da transação): rode as consultas 1.1 e 1.3. Esperado em 1.1:
--      REUNIAO 33, TRANSCRICAO 27, ANALISE 27, TEMA 47, CITACAO 60, EVENTO_TEMA 1, COMPROMISSO 8,
--      NOTIFICACAO 0. A 1.3 tem de bater com o que você anotou antes.

-- 2.11 FIM. Por padrão, desfaz tudo:
ROLLBACK;

-- Para gravar de verdade: confira os números do passo 2.10, comente a linha "ROLLBACK;" acima e
-- descomente a linha "COMMIT;" abaixo. Faça isso de propósito, depois do backup.
-- COMMIT;
