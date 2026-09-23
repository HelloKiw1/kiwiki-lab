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
- `kiwiki/services.py`: verificação somente leitura de portas locais.
- `templates/`: template Jinja2 do dashboard.
- `static/`: CSS e JavaScript sem framework frontend.

O endpoint `GET /api/status` retorna todas as métricas em JSON. O navegador consulta esse endpoint a cada 5 segundos, sem recarregar a página. Cada serviço inclui `id`, `ports`, `open_ports` e `status` (`Online`, `Offline` ou `Unknown`).

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
- Fallback seguro quando bateria ou sensores de temperatura não existem.
- Leitura de bateria e temperatura por `/sys/class/power_supply/` e `/sys/class/thermal/` quando disponíveis.
- Estado independente de Kiwiki Lab, Nginx, Django / Codex, SSH, PostgreSQL,
  MySQL/MariaDB e Redis por conexão TCP local.
- Nenhum endpoint executa comandos shell ou ações administrativas.

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
