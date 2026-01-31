# Textual Inversion (TI) ハッシュ重複および欠落問題の修正報告書

## 概要
本報告書は、Stable Diffusion Web UI において、Textual Inversion (TI) のハッシュが `png info` に重複して表示される問題、および negative プロンプトに設定された TI ハッシュが `png info` から欠落する問題の調査と修正についてまとめたものです。

## 問題の原因

### 1. TIハッシュの重複
`modules\sd_hijack_clip.py` の `TextConditionalModel.forward` メソッドにおいて、`extra_generation_params["TI hashes"]` に TI ハッシュを追加する際、既存の値をクリアせずに `hashes.append()` で追加していたため、複数回処理が行われるとハッシュが重複して記録されていました。

### 2. NegativeプロンプトのTIハッシュ欠落
`TextConditionalModel.forward` メソッドが positive プロンプトと negative プロンプトに対して別々に呼び出される際、`extra_generation_params["TI hashes"]` が毎回上書きされていたため、最後に処理されたプロンプト（通常は positive プロンプト）の TI ハッシュのみが残り、negative プロンプトのハッシュが欠落していました。

## 修正内容

### 1. TIハッシュの重複修正
`modules\sd_hijack_clip.py` の `TextConditionalModel.forward` メソッド内の以下のコードを修正しました。

```diff
<<<<<<< SEARCH
:start_line:241
-------
                self.hijack.extra_generation_params["TI hashes"] = ", ".join(hashes)
=======
                existing_hashes = set()
                if self.hijack.extra_generation_params.get("TI hashes"):
                    existing_hashes.update(self.hijack.extra_generation_params["TI hashes"].split(", "))

                existing_hashes.update(hashes)
                self.hijack.extra_generation_params["TI hashes"] = ", ".join(sorted(list(existing_hashes)))
>>>>>>> REPLACE
```
この修正により、既存のハッシュと新しく収集されたハッシュをセットで結合し、重複を排除した上で `extra_generation_params["TI hashes"]` に設定するように変更しました。

## 検証結果
修正後、positive プロンプトと negative プロンプトに異なる TI を設定して画像を生成し、`png info` を確認した結果、両方の TI ハッシュが重複なく正しく表示されることを確認しました。これにより、問題は完全に解決されました。
