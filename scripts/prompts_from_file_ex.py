import copy
import random
import gradio as gr
import os

import modules.scripts as scripts

from modules import sd_samplers, errors, sd_models
from modules.processing import Processed, process_images
from modules.shared import state

class Script(scripts.Script):
    def title(self):
        return "Prompts from file (Extended)"

    def ui(self, is_img2img):
        with gr.Group():
            prompt_txt = gr.Textbox(label="List of prompt inputs (Chunk String)", lines=1, elem_id=self.elem_id("prompt_txt"))
            file = gr.File(label="Upload prompt inputs", type='binary', elem_id=self.elem_id("file"))

        # ファイルアップロード時の処理
        file.change(fn=self.load_chunk_file, inputs=[file], outputs=[file, prompt_txt, prompt_txt], show_progress=False)
        # テキストボックスの内容変更時の処理
        prompt_txt.change(lambda tb: gr.update(lines=7) if ("\n" in tb) else gr.update(lines=2), inputs=[prompt_txt], outputs=[prompt_txt], show_progress=False)

        return [file, prompt_txt]

    def load_chunk_file(self, file):
        if file is None:
            return None, gr.update(), gr.update(lines=7)
        else:
            lines = [x.strip() for x in file.decode('utf8', errors='ignore').split("\n")]
            return None, "\n".join(lines), gr.update(lines=7)

    def process_chunk_string(self, chunk_string: str):
        """
        チャンク文字列をプロンプトリストに変換する
        """
        processed_sections = []
        content = chunk_string.splitlines()
        content_length = len(content)
        i = 0
        while i < content_length:
            tmp_line = []
            if content[i].strip().startswith('#'):
                tmp_line.append(content[i]) # #で始まる行を追加)
                i += 1
                while True:
                    if i >= content_length:
                        if len(tmp_line) > 0:
                            processed_sections.append(tmp_line)
                        break
                    elif content[i].strip().startswith('#'):
                        processed_sections.append(tmp_line)
                        break
                    else:
                        if content[i].strip():
                            tmp_line.append(content[i]) # 改行文字・空白文字を無視しない
                        i += 1
            else:
                i += 1 # #で始まらない行はスキップ

        output_prompts = []
        for genarr in processed_sections:
            gentext = ',\n'.join(genarr).replace(',,', ',').replace(',  ', ', ')
            gentext = gentext.strip().strip(',')
            output_prompts.append(gentext)
        return output_prompts

    def run(self, p, file, prompt_txt: str):
        if file is not None:
            chunk_string = file.decode('utf8', errors='ignore')
        else:
            chunk_string = prompt_txt

        if not chunk_string:
            return Processed(p, [], p.seed, "")

        prompts = self.process_chunk_string(chunk_string)

        p.do_not_save_grid = True

        job_count = 0
        jobs = []

        for prompt_line in prompts:
            # ここではコマンドライン引数処理は行わない
            args = {"prompt": prompt_line}
            job_count += args.get("n_iter", p.n_iter)
            jobs.append(args)

        print(f"Will process {len(prompts)} lines in {job_count} jobs.")
        if p.seed == -1:
            p.seed = int(random.randrange(4294967294))

        state.job_count = job_count

        images = []
        all_prompts = []
        infotexts = []
        for args in jobs:
            state.job = f"{state.job_no + 1} out of {state.job_count}"

            copy_p = copy.copy(p)
            for k, v in args.items():
                if k == "sd_model":
                    copy_p.override_settings['sd_model_checkpoint'] = v
                else:
                    setattr(copy_p, k, v)

            # プロンプトの結合ロジックはprompts_from_file.pyから変更なし
            if args.get("prompt") and p.prompt:
                copy_p.prompt = args.get("prompt") + " " + p.prompt

            if args.get("negative_prompt") and p.negative_prompt:
                copy_p.negative_prompt = p.negative_prompt + " " + args.get("negative_prompt")

            proc = process_images(copy_p)
            images += proc.images
            all_prompts += proc.all_prompts
            infotexts += proc.infotexts

        return Processed(p, images, p.seed, "", all_prompts=all_prompts, infotexts=infotexts)
