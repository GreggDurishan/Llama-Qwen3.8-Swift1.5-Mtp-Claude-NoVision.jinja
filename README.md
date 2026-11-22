Llama-Qwen3.8-Swift1.5-Mtp-Claude-NoVision.jinja

A Jinja chat template for use with Claude Code and Swift 1.5 or Qwen 3.8 MTP ggufs in Llama-server
adapted from froggeric/Qwen-Fixed-Chat-Templates (https://huggingface.co/froggeric/Qwen-Fixed-Chat-Templates/discussions/110/files)


an example tuned llama-server call on a 9600x 32gb ddr5 9060xt 16gb:

llama-server -m Swift-1.5-Qwen3.8-27B-GSQ-RCO-IQ3_XXS-mtp.gguf --threads 6 --parallel 1 --load-mode none --flash-attn on
--reasoning-effort medium --temp 0.7 --top-k 20 --top-p 0.95 --min-p 0.0 --spec-type draft-mtp --spec-draft-n-max 9 
--spec-draft-p-min 0.72 --jinja --chat-template-file Llama-Qwen3.8-Swift1.5-Mtp-Claude-NoVision.jinja 
--cache-type-k q5_0 --cache-type-v q4_1 --batch-size 1024 --ubatch-size 512 --fit-target 512

136k context, 300-800 t/s processing, 15-40 t/s gen

I like to turn off browser graphics acceleration instead of plugging the monitor into onboard graphics.
