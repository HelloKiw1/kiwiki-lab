# Kiwiki Lab

Kiwiki Lab é um dashboard leve para monitorar um servidor pessoal, pensado para rodar continuamente em um smartphone Android reaproveitado como servidor Linux. A aplicação também funciona durante o desenvolvimento no Windows.

## Objetivo

Exibir em um painel moderno informações do sistema em tempo real: CPU, memória, armazenamento, rede, uptime, sistema operacional, bateria, temperaturas e estado de serviços locais.

## Arquitetura

- `app.py`: ponto de entrada da aplicação Flask.
- `kiwiki/__init__.py`: factory da aplicação e rotas HTTP.
- `kiwiki/system.py`: CPU, memória, armazenamento, uptime e informações do sistema.
- `kiwiki/battery.py`: bateria e sensores térmicos, com fallback para sysfs em Linux/Android.
- `kiwiki/network.py`: endereço IP e contadores de rede.
- `kiwiki/host_agent.py`: consulta opcional ao Host Agent local do Termux.
- `kiwiki/history.py`: SQLite, coleta periódica, agregação horária e retenção.
- `kiwiki/services.py`: verificação somente leitura de portas locais.
- `templates/`: template Jinja2 do dashboard.
- `static/`: CSS e JavaScript sem framework frontend.

O endpoint `GET /api/status` retorna todas as métricas em JSON. O navegador consulta esse endpoint a cada 5 segundos, sem recarregar a página. Cada serviço inclui `id`, `ports`, `open_ports` e `status` (`Online`, `Offline` ou `Unknown`). O uptime exibido pelo dashboard vem do `agent_uptime_seconds` do Host Agent e é identificado como `host_agent`.

O endpoint `GET /api/history/summary?range=1h|6h|24h|7d` fornece pontos prontos
para os gráficos. O banco é criado automaticamente em `data/history.db`.
Dados brutos são coletados a cada 60 segundos e retidos por 7 dias. A tabela
horária mantém médias, mínimos, máximos e totais de tráfego por 90 dias.

## Dependências

- Python 3.10 ou mais recente
- Flask 3
- psutil

As dependências Python estão declaradas em `requirements.txt`.

## Instalação e execução no Windows

No PowerShell, a partir da pasta do projeto:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python app.py
```

Abra <http://127.0.0.1:5000> no navegador. Se a política do PowerShell impedir a ativação, use diretamente `.\.venv\Scripts\python.exe app.py`.

## Execução no Linux / Android Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python app.py
```

O Flask escuta localmente por padrão. Configuração de Nginx, domínio e deploy fica para uma etapa futura.

## Funcionalidades atuais

- Dashboard escuro, responsivo e sem bibliotecas frontend externas.
- Atualização automática de métricas a cada 5 segundos.
- Histórico local em SQLite com gráficos de CPU, RAM, temperatura, bateria e rede.
- Retenção automática de dados detalhados por 7 dias e agregados por hora por 90 dias.
- Fallback seguro quando bateria ou sensores de temperatura não existem.
- Leitura de bateria e temperatura por `/sys/class/power_supply/` e `/sys/class/thermal/` quando disponíveis.
- Integração opcional com `http://127.0.0.1:9100/status` para dados reais do Android, Wi-Fi e bateria.
- Estado independente de Kiwiki Lab, Nginx, Django / Codex, SSH e PostgreSQL
  por conexão TCP local.
- Nenhum endpoint executa comandos shell ou ações administrativas.

Quando o Host Agent está disponível, seus dados são usados primeiro para bateria,
Wi-Fi, rede e dispositivo. Se ele estiver offline, o Kiwiki Lab usa os coletores
locais existentes e exibe `Not available` onde não houver fallback.

## Adicionar serviços

Edite `SERVICES` em `kiwiki/services.py`, adicionando uma instância de
`ServiceConfig` com o nome e as portas locais. Cada serviço é verificado de
forma independente e será incluído automaticamente no dashboard. A estrutura
também reserva `process_names` e `systemd_unit` para futuras verificações
somente leitura.

## Próximos passos

- Configuração de serviços por ambiente, sem alterar código.
- Autenticação e proteção de acesso antes de uma exposição externa.
- Histórico de métricas e alertas.
- Integração com informações específicas do Android, quando disponíveis.
