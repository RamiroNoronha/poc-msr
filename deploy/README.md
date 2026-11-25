# Deploy numa VM do Azure (Azure for Students)

Front e backend rodam na mesma máquina com Docker Compose. O **Caddy** serve o front, encaminha `/api` para o backend e emite o certificado HTTPS sozinho. Assim fica **uma URL só** para compartilhar, sem problema de CORS.

Escolhemos uma VM (e não App Service ou Container Apps) porque a primeira mineração de um repositório grande leva minutos. Os serviços gerenciados do Azure cortam requisições HTTP depois de cerca de 4 minutos, e a VM não tem esse limite.

## 1. Criar a VM (portal do Azure)

1. Ative o **Azure for Students** com o e-mail da universidade.
2. **Máquinas virtuais → Criar**:
   - **Imagem:** Ubuntu Server 24.04 LTS.
   - **Região:** Brazil South (ou a mais próxima com o tamanho disponível).
   - **Tamanho:** `B1s` costuma estar nos serviços gratuitos de 12 meses. Para repositórios grandes, `B2s` (4 GB) é mais folgado e consome o crédito.
   - **Autenticação:** chave SSH.
   - **Portas de entrada:** SSH (22), HTTP (80) e HTTPS (443).
3. Depois de criada, abra o **IP público → Configuração** e defina um **rótulo de nome DNS** (ex.: `poc-msr`). O endereço fica `poc-msr.<regiao>.cloudapp.azure.com`; é ele que vai no `SITE_ADDRESS`.

## 2. Preparar a máquina

```bash
ssh azureuser@poc-msr.<regiao>.cloudapp.azure.com

# Docker
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker $USER && newgrp docker

# Swap de 2 GB: ajuda a B1s (1 GB de RAM) a minerar repositórios maiores
sudo fallocate -l 2G /swapfile && sudo chmod 600 /swapfile && sudo mkswap /swapfile && sudo swapon /swapfile
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```

## 3. Subir a aplicação

```bash
git clone https://github.com/RamiroNoronha/poc-msr.git
git clone https://github.com/RamiroNoronha/poc-msr-front.git

cd poc-msr/deploy
cp .env.example .env
nano .env   # GITHUB_TOKEN e SITE_ADDRESS

docker compose up -d --build
docker compose logs -f
```

Abra `https://<SITE_ADDRESS>`. O certificado pode levar alguns segundos na primeira vez.

## Atualizar depois de um push

```bash
cd ~/poc-msr && git pull && cd ~/poc-msr-front && git pull
cd ~/poc-msr/deploy && docker compose up -d --build
```

## Limites e segurança

- Só aceita `https://github.com/<dono>/<repositorio>` público.
- `MAX_REPO_SIZE_MB` (padrão 500) recusa repositórios maiores, usando o tamanho informado pela API do GitHub.
- `GIT_TIMEOUT_SECONDS` (padrão 600) limita o clone e o `git log`.
- O backend não fica exposto: só o Caddy (portas 80/443) recebe conexões.
- As análises são feitas uma por vez (fila única). Com várias pessoas ao mesmo tempo, uma espera a outra.
- O `GITHUB_TOKEN` fica só no `.env` da VM. Use um token *fine-grained* sem permissões extras (acesso público, somente leitura).

## Custos

Desligue a VM (**Parar**, no portal) quando não estiver em uso, para não gastar crédito. O IP e o nome DNS continuam reservados se o IP for **estático**.
