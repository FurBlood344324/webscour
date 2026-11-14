This article has multiple issues. Please help [improve it](https://en.wikipedia.org/wiki/Special:EditPage/Transformer_%28deep_learning%29) or discuss these issues on the [talk page](https://en.wikipedia.org/wiki/Talk:Transformer_%28deep_learning%29). _([Learn how and when to remove these messages](https://en.wikipedia.org/wiki/Help:Maintenance_template_removal))_

![icon](https://thumb.wikimedia.org/wikipedia/en/thumb/9/99/Question_book-new.svg/60px-Question_book-new.svg.png?utm_source=en.wikipedia.org&utm_campaign=parser&utm_content=thumbnail)

This article needs [more citations](https://en.wikipedia.org/wiki/Wikipedia:Verifiability).

Please help improve this article by adding citations to reliable sources. Unsourced material may be challenged and removed._Find sources:_ ["Transformer" deep learning](https://www.google.com/search?as_eq=wikipedia&q=%22Transformer%22+deep+learning) – [news](https://www.google.com/search?tbm=nws&q=%22Transformer%22+deep+learning+-wikipedia&tbs=ar:1) **·** [newspapers](https://www.google.com/search?&q=%22Transformer%22+deep+learning&tbs=bkt:s&tbm=bks) **·** [books](https://www.google.com/search?tbs=bks:1&q=%22Transformer%22+deep+learning+-wikipedia) **·** [scholar](https://scholar.google.com/scholar?q=%22Transformer%22+deep+learning) **·** [JSTOR](https://www.jstor.org/action/doBasicSearch?Query=%22Transformer%22+deep+learning&acc=on&wc=on)

(June 2026)

([Learn how and when to remove this message](https://en.wikipedia.org/wiki/Help:Maintenance_template_removal))

![](https://thumb.wikimedia.org/wikipedia/commons/thumb/a/a4/Text_document_with_red_question_mark.svg/40px-Text_document_with_red_question_mark.svg.png?utm_source=en.wikipedia.org&utm_campaign=parser&utm_content=thumbnail)

Some of this article's listed sources may not be [reliable](https://en.wikipedia.org/wiki/Wikipedia:Reliable_sources).

Please help improve this article by looking for better, more reliable sources. Unreliable citations may be challenged and removed.

(June 2026)

([Learn how and when to remove this message](https://en.wikipedia.org/wiki/Help:Maintenance_template_removal))

([Learn how and when to remove this message](https://en.wikipedia.org/wiki/Help:Maintenance_template_removal))

| Part of [a series](https://en.wikipedia.org/wiki/Category:Machine_learning) on |
| --- |
| [Machine learning](https://en.wikipedia.org/wiki/Machine_learning)and[data mining](https://en.wikipedia.org/wiki/Data_mining) |
|  |
|  |
|  |
|  |
|  |
|  |
|  |
|  |
|  |
| Learning with humans |
| Model diagnostics |
|  |
|  |
|  |
|  |

In [deep learning](https://en.wikipedia.org/wiki/Deep_learning), the **transformer** is a family of [artificial neural network](https://en.wikipedia.org/wiki/Artificial_neural_network) architectures based on the multi-head [attention](https://en.wikipedia.org/wiki/Attention_%28machine_learning%29) mechanism, in which input data such as text, images, or audio is converted to a sequence of numerical representations called [tokens](https://en.wikipedia.org/wiki/Large_language_model#Tokenization), and each token is converted into a vector through an embedding layer.[\[1\]](https://en.wikipedia.org/wiki/Transformer_%28deep_learning%29#cite_note-2017_Attention_Is_All_You_Need-1) At each layer, each [token](https://en.wikipedia.org/wiki/Tokenization_%28lexical_analysis%29) is then [contextualized](https://en.wikipedia.org/wiki/Contextualization_%28computer_science%29) within the scope of the [context window](https://en.wikipedia.org/wiki/Context_window) with other (unmasked) tokens via a parallel multi-head attention mechanism, allowing the signal for key tokens to be amplified and less important tokens to be diminished. Because self-attention alone is permutation-invariant, transformers inject positional information, typically through [positional encodings](https://en.wikipedia.org/wiki/Positional_encoding) or learned positional embeddings, so token order can affect the output.[\[1\]](https://en.wikipedia.org/wiki/Transformer_%28deep_learning%29#cite_note-2017_Attention_Is_All_You_Need-1)

Because transformers do not process tokens one at a time, their computations can be parallelized across sequence positions during training more readily than those of recurrent neural networks like [long short-term memory](https://en.wikipedia.org/wiki/Long_short-term_memory) (LSTM).[\[2\]](https://en.wikipedia.org/wiki/Transformer_%28deep_learning%29#cite_note-lstm1997-2) Later variations have been widely adopted for training [large language models](https://en.wikipedia.org/wiki/Large_language_model) (LLMs) on large (language) [datasets](https://en.wikipedia.org/wiki/Training,_validation,_and_test_data_sets).\[_[citation needed](https://en.wikipedia.org/wiki/Wikipedia:Citation_needed)_\]

The original version of the transformer architecture was proposed in the 2017 paper "[Attention Is All You Need](https://en.wikipedia.org/wiki/Attention_Is_All_You_Need)" by researchers at [Google](https://en.wikipedia.org/wiki/Google).[\[1\]](https://en.wikipedia.org/wiki/Transformer_%28deep_learning%29#cite_note-2017_Attention_Is_All_You_Need-1) The predecessors of transformers were developed as an improvement over previous architectures for [machine translation](https://en.wikipedia.org/wiki/Machine_translation),[\[3\]](https://en.wikipedia.org/wiki/Transformer_%28deep_learning%29#cite_note-inventors-3)[\[4\]](https://en.wikipedia.org/wiki/Transformer_%28deep_learning%29#cite_note-inventconfirm-4) but have found many applications since. They are used in large-scale [natural language processing](https://en.wikipedia.org/wiki/Natural_language_processing), [computer vision](https://en.wikipedia.org/wiki/Computer_vision) ([vision transformers](https://en.wikipedia.org/wiki/Vision_transformer)), [reinforcement learning](https://en.wikipedia.org/wiki/Reinforcement_learning),[\[5\]](https://en.wikipedia.org/wiki/Transformer_%28deep_learning%29#cite_note-5) [audio](https://en.wikipedia.org/wiki/Audio_signal_processing),[\[6\]](https://en.wikipedia.org/wiki/Transformer_%28deep_learning%29#cite_note-Robust_Speech_Recognition_via_Large-Scale_Weak_Supervision-6) [multimodal learning](https://en.wikipedia.org/wiki/Multimodal_learning), [robotics](https://en.wikipedia.org/wiki/Robotics),[\[7\]](https://en.wikipedia.org/wiki/Transformer_%28deep_learning%29#cite_note-7) and playing [chess](https://en.wikipedia.org/wiki/Computer_chess).[\[8\]](https://en.wikipedia.org/wiki/Transformer_%28deep_learning%29#cite_note-grandmaster-8) It has also led to the development of [pre-trained systems](https://en.wikipedia.org/wiki/Transfer_learning), such as [generative pre-trained transformers](https://en.wikipedia.org/wiki/Generative_pre-trained_transformer) (GPTs).[\[9\]](https://en.wikipedia.org/wiki/Transformer_%28deep_learning%29#cite_note-wolf2020-9)

## History

This section's style of writing may not reflect the [encyclopedic tone](https://en.wikipedia.org/wiki/Wikipedia:Writing_better_articles#Tone) used on Wikipedia.

See Wikipedia's guide to writing better articles for suggestions.

(February 2026)

([Learn how and when to remove this message](https://en.wikipedia.org/wiki/Help:Maintenance_template_removal))

See also: Timeline of machine learning

### Predecessors

Before transformers, [recurrent neural networks](https://en.wikipedia.org/wiki/Recurrent_neural_network) (RNNs) were widely used for sequence modelling and generation. A well-cited early example was the [Elman network](https://en.wikipedia.org/wiki/Elman_network) (1990). In theory, the information from one token can propagate arbitrarily far down the sequence, but in practice the [vanishing-gradient problem](https://en.wikipedia.org/wiki/Vanishing-gradient_problem) leaves the model's state at the end of a long sentence without precise, extractable information about preceding tokens.

A key breakthrough was [LSTM](https://en.wikipedia.org/wiki/Long_short-term_memory) (originally described in a 1995 technical report and formally published in 1997),[\[2\]](https://en.wikipedia.org/wiki/Transformer_%28deep_learning%29#cite_note-lstm1997-2)[\[note 1\]](https://en.wikipedia.org/wiki/Transformer_%28deep_learning%29#cite_note-10) an RNN that introduced gating mechanisms to mitigate the vanishing gradient problem, allowing efficient learning of long-sequence modelling. One key architectural element was the use of _multiplicative gating units_, in which the outputs of some neurons modulate the outputs of others. These multiplicative units are conceptually distinct from the additive attention mechanism later introduced for sequence-to-sequence models. [\[10\]](https://en.wikipedia.org/wiki/Transformer_%28deep_learning%29#cite_note-11) Neural networks using multiplicative units were later called _sigma-pi networks_[\[11\]](https://en.wikipedia.org/wiki/Transformer_%28deep_learning%29#cite_note-PDP-12) or _[higher-order networks](https://en.wikipedia.org/wiki/Higher-order_neural_network?action=edit&redlink=1)_.[\[12\]](https://en.wikipedia.org/wiki/Transformer_%28deep_learning%29#cite_note-13) LSTM became the standard architecture for long sequence modelling until the 2017 publication of transformers. However, LSTM still used sequential processing, like most other RNNs.[\[note 2\]](https://en.wikipedia.org/wiki/Transformer_%28deep_learning%29#cite_note-14) Specifically, RNNs operate one token at a time from first to last; they cannot operate in parallel over all tokens in a sequence.

Transformers allow parallel processing of tokens during training, but standard self-attention has computational and memory costs that grow quadratically with sequence length.

### Attention with seq2seq

Main article: Seq2seq § History

The idea of encoder–decoder sequence transduction had been developed in the early 2010s; commonly cited as the originators that produced seq2seq are two concurrently published papers from 2014.[\[13\]](https://en.wikipedia.org/wiki/Transformer_%28deep_learning%29#cite_note-:22-15)[\[14\]](https://en.wikipedia.org/wiki/Transformer_%28deep_learning%29#cite_note-sequence-16)\[_[original research?](https://en.wikipedia.org/wiki/Wikipedia:No_original_research)_\]

A 380M-parameter model for machine translation uses two [long short-term memories](https://en.wikipedia.org/wiki/Long_short-term_memory) (LSTM).[\[14\]](https://en.wikipedia.org/wiki/Transformer_%28deep_learning%29#cite_note-sequence-16) Its architecture consists of two parts. The _encoder_ is an LSTM that takes in a sequence of tokens and turns it into a vector. The _decoder_ is another LSTM that converts the vector into a sequence of tokens. Similarly, another 130M-parameter model used [gated recurrent units](https://en.wikipedia.org/wiki/Gated_recurrent_unit) (GRU) instead of LSTM.[\[13\]](https://en.wikipedia.org/wiki/Transformer_%28deep_learning%29#cite_note-:22-15) Later research showed that GRUs are neither better nor worse than LSTMs for seq2seq.[\[15\]](https://en.wikipedia.org/wiki/Transformer_%28deep_learning%29#cite_note-MyUser_Arxiv.org_May_18_2016c-17)[\[16\]](https://en.wikipedia.org/wiki/Transformer_%28deep_learning%29#cite_note-gruber_jockisch-18)

These early seq2seq models had no attention mechanism, and the state vector is accessible only after the _last_ word of the source text was processed. Although in theory such a vector retains the information about the whole original sentence, in practice the information is poorly preserved. This is because the input is processed sequentially by one recurrent network into a _fixed_-size output vector, which is then processed by another recurrent network into an output. If the input is long, then the output vector would not be able to contain all relevant information, degrading the output. As evidence, reversing the input sentence improved seq2seq translation.[\[17\]](https://en.wikipedia.org/wiki/Transformer_%28deep_learning%29#cite_note-19)

The _RNN search_ model introduced an attention mechanism to seq2seq for machine translation to solve the bottleneck problem (of the _fixed-size_ output vector), allowing the model to process long-distance dependencies more easily. The name is because it "emulates searching through a source sentence during decoding a translation".[\[3\]](https://en.wikipedia.org/wiki/Transformer_%28deep_learning%29#cite_note-inventors-3)

The relative performances were compared between global (that of _RNN search_) and local (sliding window) attention model architectures for machine translation, finding that mixed attention had higher quality than global attention, while local attention reduced translation time.[\[18\]](https://en.wikipedia.org/wiki/Transformer_%28deep_learning%29#cite_note-20)

In 2016, [Google Translate](https://en.wikipedia.org/wiki/Google_Translate) was revamped to [Google Neural Machine Translation](https://en.wikipedia.org/wiki/Google_Neural_Machine_Translation), which replaced the previous model based on [statistical machine translation](https://en.wikipedia.org/wiki/Statistical_machine_translation). The GNMT system was a sequence-to-sequence model with eight LSTM layers in its encoder and eight in its decoder. The first encoder layer was bidirectional, the remaining seven encoder layers were unidirectional, and all eight decoder layers were unidirectional.[\[19\]](https://en.wikipedia.org/wiki/Transformer_%28deep_learning%29#cite_note-Y4moj-21) It took nine months to develop, and it outperformed the statistical approach, which took ten years to develop.[\[20\]](https://en.wikipedia.org/wiki/Transformer_%28deep_learning%29#cite_note-UJDu8-22)

### Parallelizing attention

Main article: Attention (machine learning) § History

Seq2seq models with attention (including self-attention) still suffered from the same issue with recurrent networks, which is that they are hard to [parallelize](https://en.wikipedia.org/wiki/Parallel_computing), which prevented them from being accelerated on GPUs. In 2016, _decomposable attention_ applied a self-attention mechanism to [feedforward networks](https://en.wikipedia.org/wiki/Feedforward_neural_network), which are easy to parallelize, and achieved state-of-the-art ([SOTA](https://en.wikipedia.org/wiki/State_of_the_art)) results in [textual entailment](https://en.wikipedia.org/wiki/Textual_entailment) with an order of magnitude fewer parameters than LSTMs.[\[21\]](https://en.wikipedia.org/wiki/Transformer_%28deep_learning%29#cite_note-23) One of its authors, Jakob Uszkoreit, suspected that attention _without_ recurrence would be sufficient for language translation, thus the title "attention is _All_ you need".[\[22\]](https://en.wikipedia.org/wiki/Transformer_%28deep_learning%29#cite_note-:11-24) That hypothesis was against conventional wisdom at the time, and even his father [Hans Uszkoreit](https://en.wikipedia.org/wiki/Hans_Uszkoreit), a well-known computational linguist, was skeptical.[\[22\]](https://en.wikipedia.org/wiki/Transformer_%28deep_learning%29#cite_note-:11-24) In the same year, self-attention (called _intra-attention or_ _intra-sentence attention_) was proposed for LSTMs.[\[23\]](https://en.wikipedia.org/wiki/Transformer_%28deep_learning%29#cite_note-25)

The original encoder–decoder Transformer was introduced in the paper "[Attention Is All You Need](https://en.wikipedia.org/wiki/Attention_is_all_you_need)," submitted to arXiv on 2017-06-12. At the time, the focus of the research was on improving [seq2seq](https://en.wikipedia.org/wiki/Seq2seq) for [machine translation](https://en.wikipedia.org/wiki/Machine_translation), by removing its recurrence to process all tokens in parallel, but preserving its dot-product attention mechanism to keep its text processing performance.[\[1\]](https://en.wikipedia.org/wiki/Transformer_%28deep_learning%29#cite_note-2017_Attention_Is_All_You_Need-1) This led to the introduction of a multi-head attention model that was easier to parallelize due to the use of independent heads and the lack of recurrence. Its parallelizability was an important factor to its widespread use in large neural networks.[\[24\]](https://en.wikipedia.org/wiki/Transformer_%28deep_learning%29#cite_note-26)

### AI boom era

Soon after developing the Transformer, researchers at Google used a decoder-only variation to generate fictitious Wikipedia articles.[\[25\]](https://en.wikipedia.org/wiki/Transformer_%28deep_learning%29#cite_note-27) Transformer architecture is now used alongside many [generative models](https://en.wikipedia.org/wiki/Generative_AI) that contribute to the ongoing [AI boom](https://en.wikipedia.org/wiki/AI_boom).

The "reference implementation" of the original Transformer was written in a TensorFlow library.[\[26\]](https://en.wikipedia.org/wiki/Transformer_%28deep_learning%29#cite_note-28)[\[27\]](https://en.wikipedia.org/wiki/Transformer_%28deep_learning%29#cite_note-29) In language modelling, [ELMo](https://en.wikipedia.org/wiki/ELMo) (2018) was a bi-directional LSTM that produces contextualized [word embeddings](https://en.wikipedia.org/wiki/Word_embedding), improving upon the line of research from [bag of words](https://en.wikipedia.org/wiki/Bag-of-words_model) and [word2vec](https://en.wikipedia.org/wiki/Word2vec). It was followed by [BERT](https://en.wikipedia.org/wiki/BERT_%28language_model%29) (2018), an encoder-only transformer model.[\[28\]](https://en.wikipedia.org/wiki/Transformer_%28deep_learning%29#cite_note-:03-30) In October 2019, Google started using BERT to process search queries.[\[29\]](https://en.wikipedia.org/wiki/Transformer_%28deep_learning%29#cite_note-31) In 2020, Google Translate replaced the previous RNN-encoder–RNN-decoder model by a transformer-encoder–RNN-decoder model.[\[30\]](https://en.wikipedia.org/wiki/Transformer_%28deep_learning%29#cite_note-gtrans-32)\[_[non-primary source needed](https://en.wikipedia.org/wiki/Wikipedia:No_original_research#Primary,_secondary_and_tertiary_sources)_\]

Starting in 2018, the OpenAI [GPT series](https://en.wikipedia.org/wiki/Generative_pre-trained_transformer) of decoder-only transformers became state of the art in [natural language generation](https://en.wikipedia.org/wiki/Natural_language_generation). At the end of 2022, [ChatGPT](https://en.wikipedia.org/wiki/ChatGPT), a chatbot based on a fine-tuned variant of GPT-3.5, became unexpectedly[\[31\]](https://en.wikipedia.org/wiki/Transformer_%28deep_learning%29#cite_note-33)[\[32\]](https://en.wikipedia.org/wiki/Transformer_%28deep_learning%29#cite_note-34) popular, triggering a boom around [large language models](https://en.wikipedia.org/wiki/Large_language_model).[\[33\]](https://en.wikipedia.org/wiki/Transformer_%28deep_learning%29#cite_note-35)

Transformers have been applied in modalities beyond text. Four days after the publication of "Attention is All You Need", a [multimodal](https://en.wikipedia.org/wiki/Multimodal_learning) transformer architecture, MultiModel, was published by most authors of that paper.[\[34\]](https://en.wikipedia.org/wiki/Transformer_%28deep_learning%29#cite_note-36) The [vision transformer](https://en.wikipedia.org/wiki/Vision_transformer) adapts the architecture to images by processing image patches as a sequence of tokens.[\[35\]](https://en.wikipedia.org/wiki/Transformer_%28deep_learning%29#cite_note-37) Transformer models are also used in systems for image and video generation, although these systems differ in how they represent and process their inputs and outputs.

## Training

### Methods for stabilizing training

The original Transformer paper used a learning-rate warmup schedule: the learning rate increased linearly for the first 4,000 training steps and then decayed according to an inverse square-root schedule.[\[1\]](https://en.wikipedia.org/wiki/Transformer_%28deep_learning%29#cite_note-2017_Attention_Is_All_You_Need-1)

A study of the Transformer found that applying [layer normalization](https://en.wikipedia.org/wiki/Layer_normalization) before the attention and feed-forward sublayers can improve training stability and reduce dependence on learning-rate warmup in some settings.[\[36\]](https://en.wikipedia.org/wiki/Transformer_%28deep_learning%29#cite_note-auto1-38) This arrangement is called pre-LN; the original Transformer used post-LN.

### Regularization

The original transformer used dropout during training to reduce overfitting. Dropout was applied to the output of each sublayer before its residual connection and normalization, as well as to the sums of token embeddings and positional encodings. The original paper also used label smoothing, which replaces a certain target distribution with one that assigns a small amount of probability to alternative tokens. These techniques can improve generalization by going against overconfidence in the training targets.[\[37\]](https://en.wikipedia.org/wiki/Transformer_%28deep_learning%29#cite_note-39)

### Distributed Training

Large transformer models are typically trained across multiple GPUs or other accelerators because their parameters, activations, and training data may not fit on a single device. Data parallelism copies the model across devices and splits different batches of training examples among them; gradients are then synchronized before parameters are updated. Model parallelism divides a model itself across devices. Tensor parallelism splits operations within individual layers, while pipeline parallelism assigns consecutive groups of layers to different devices.[\[38\]](https://en.wikipedia.org/wiki/Transformer_%28deep_learning%29#cite_note-40)

### Pretrain-finetune

Many transformer-based language models are pretrained on large corpora using self-supervised objectives, and some are later fine-tuned for specific tasks. The dataset and objective vary by model. Common pretraining objectives include:

- next-token prediction in autoregressive language models[\[39\]](https://en.wikipedia.org/wiki/Transformer_%28deep_learning%29#cite_note-:8-41)
- masked-token prediction[\[40\]](https://en.wikipedia.org/wiki/Transformer_%28deep_learning%29#cite_note-:5-42)
- span corruption or denoising, used by T5.

Downstream fine-tuning tasks can include reading comprehension, sentiment classification, paraphrasing, and summarization.

The [T5 transformer](https://en.wikipedia.org/wiki/T5_%28language_model%29) report[\[41\]](https://en.wikipedia.org/wiki/Transformer_%28deep_learning%29#cite_note-Raffel_Shazeer_2020_Exploring_the_Limits-43) documents a large number of [natural language](https://en.wikipedia.org/wiki/Natural_language) pretraining tasks. Some examples are:

- restoring or repairing incomplete or corrupted text. For example, the input, "Thank you ~~ me to your party ~~ week", might generate the output, "Thank you **for inviting** me to your party **last** week".
- translation between natural languages (machine translation)
- judging the pragmatic acceptability of natural language. For example, the following sentence might be judged "not acceptable",[\[42\]](https://en.wikipedia.org/wiki/Transformer_%28deep_learning%29#cite_note-44) because even though it is syntactically well-formed, it is improbable in ordinary human usage: The course is jumping well.

While each of these tasks is trivial or obvious for human native speakers of the language (or languages), they have typically proved challenging for previous generations of machine learning architecture.

### Knowledge distillation

Main article: Knowledge distillation

Knowledge distillation is a method for training a smaller model, called a "student", to reproduce the output behavior of a larger "teacher" model. In transformer models, the student can be trained using the teacher's output probability distribution, intermediate representations, or attention patterns in addition to the original training labels. Distillation can lower computational and memory requirements of deployment while keeping most of the teacher model's performance on a specified task.\[_[citation needed](https://en.wikipedia.org/wiki/Wikipedia:Citation_needed)_\]

### Tasks

See also: Large language model § Evaluation

In general, there are three classes of language modelling tasks: "masked",[\[40\]](https://en.wikipedia.org/wiki/Transformer_%28deep_learning%29#cite_note-:5-42) "autoregressive",[\[39\]](https://en.wikipedia.org/wiki/Transformer_%28deep_learning%29#cite_note-:8-41) and "prefixLM".[\[43\]](https://en.wikipedia.org/wiki/Transformer_%28deep_learning%29#cite_note-:4-45) These classes are independent of a specific modeling architecture such as transformer, but they are often discussed in the context of transformer.

In a masked task,[\[40\]](https://en.wikipedia.org/wiki/Transformer_%28deep_learning%29#cite_note-:5-42) one or more of the tokens is masked out, and the model would produce a probability distribution predicting what the masked-out tokens are based on the context. The [loss function](https://en.wikipedia.org/wiki/Loss_function) for the task is typically sum of [log-perplexities](https://en.wikipedia.org/wiki/Perplexity) for the masked-out tokens: and the model is trained to minimize this loss function. The [BERT series of models](https://en.wikipedia.org/wiki/BERT_%28language_model%29) are trained for masked token prediction and another task. ("Masked" as in "masked language modelling" is not "masked" as in "[masked attention](https://en.wikipedia.org/wiki/Transformer_%28deep_learning%29#Masked_attention)".)

In an autoregressive task,[\[39\]](https://en.wikipedia.org/wiki/Transformer_%28deep_learning%29#cite_note-:8-41) the model predicts each token from the preceding context. During training, a causal attention mask prevents each position from attending to later tokens, allowing the sequence to be processed in parallel while the loss is computed for target tokens. During inference, tokens are generated one or more at a time and appended to the context. The [GPT series of models](https://en.wikipedia.org/wiki/Generative_pre-trained_transformer) are trained with autoregressive objectives.

In a prefix-language-modeling task, the model receives a prefix as context and predicts a continuation. Depending on the architecture and mask, prefix tokens may attend to one another bidirectionally while each continuation token can attend only to the prefix and earlier continuation tokens. T5 is an encoder–decoder model trained primarily with span-corruption objectives, rather than this prefix-LM objective.[\[41\]](https://en.wikipedia.org/wiki/Transformer_%28deep_learning%29#cite_note-Raffel_Shazeer_2020_Exploring_the_Limits-43)

## Architecture

![icon](https://thumb.wikimedia.org/wikipedia/en/thumb/9/99/Question_book-new.svg/60px-Question_book-new.svg.png?utm_source=en.wikipedia.org&utm_campaign=parser&utm_content=thumbnail)

This section does not [cite](https://en.wikipedia.org/wiki/Wikipedia:Citing_sources) any [sources](https://en.wikipedia.org/wiki/Wikipedia:Verifiability).

Please help improve this section by adding citations to reliable sources. Unsourced material may be challenged and removed._Find sources:_ ["Transformer" deep learning](https://www.google.com/search?as_eq=wikipedia&q=%22Transformer%22+deep+learning) – [news](https://www.google.com/search?tbm=nws&q=%22Transformer%22+deep+learning+-wikipedia&tbs=ar:1) **·** [newspapers](https://www.google.com/search?&q=%22Transformer%22+deep+learning&tbs=bkt:s&tbm=bks) **·** [books](https://www.google.com/search?tbs=bks:1&q=%22Transformer%22+deep+learning+-wikipedia) **·** [scholar](https://scholar.google.com/scholar?q=%22Transformer%22+deep+learning) **·** [JSTOR](https://www.jstor.org/action/doBasicSearch?Query=%22Transformer%22+deep+learning&acc=on&wc=on)

(October 2026)

([Learn how and when to remove this message](https://en.wikipedia.org/wiki/Help:Maintenance_template_removal))

Transformer architectures vary, but many include some of the following components:

- A tokenizer, which maps input data to tokens or other discrete units.
- An embedding or input-projection layer, which maps those units to vectors and may add positional information.
- One or more attention and feed-forward layers. Encoder-only, decoder-only, and encoder–decoder models use different arrangements of these layers.
- An output layer appropriate to the task, such as a vocabulary projection for language modeling.

The following description focuses on the encoder–decoder Transformer introduced in the original paper; other variants are described in the [following section](https://en.wikipedia.org/wiki/Transformer_%28deep_learning%29#Subsequent_work).

By convention, we write all vectors as row vectors. For example, pushing a vector through a linear layer means multiplying it by a weight matrix on the right, as .

### Tokenization

Tokenization maps input text to a sequence of token identifiers drawn from a vocabulary. Depending on the tokenizer, preprocessing may normalize text and divide it into words, subwords, or bytes. Subword methods such as [byte pair encoding](https://en.wikipedia.org/wiki/Byte_pair_encoding) (BPE) and the unigram language model can represent many rare or previously unseen words as sequences of known units, rather than requiring a single `[UNK]` token. A tokenizer's vocabulary is learned or otherwise specified before it is used.[\[44\]](https://en.wikipedia.org/wiki/Transformer_%28deep_learning%29#cite_note-46)[\[45\]](https://en.wikipedia.org/wiki/Transformer_%28deep_learning%29#cite_note-47)

### Embedding

Further information: Word embedding

Each integer token identifier is converted into an embedding vector via a [lookup table](https://en.wikipedia.org/wiki/Lookup_table). Equivalently stated, it multiplies a [one-hot](https://en.wikipedia.org/wiki/One-hot) representation of the token identifier by an embedding matrix . For example, if the input token's identifier is , then the one-hot representation is , and its embedding vector isThe token embedding vectors are added to their respective positional encoding vectors (see below), producing the sequence of input vectors.

The dimension of an embedding vector is called _hidden size_ or _embedding size_ and written as .[\[28\]](https://en.wikipedia.org/wiki/Transformer_%28deep_learning%29#cite_note-:03-30) This size is written as  in the original transformer paper.[\[1\]](https://en.wikipedia.org/wiki/Transformer_%28deep_learning%29#cite_note-2017_Attention_Is_All_You_Need-1)

### Un-embedding

An un-embedding layer is almost the reverse of an embedding layer. Whereas an embedding layer converts a token identifier into a vector, an un-embedding layer converts a vector into a probability distribution over tokens.

The un-embedding layer is a linear-[softmax](https://en.wikipedia.org/wiki/Softmax_function) layer:The matrix has shape . Some architectures use the transpose of the embedding matrix  as the un-embedding matrix  in order to avoid needing double the amount of embedding-related parameters and to avoid divergence during training. This practice is called _weight tying_.

### Positional encoding

Main article: Positional encoding

A positional encoding or embedding supplies information about token position or order. The original Transformer added fixed sinusoidal position encodings to token embeddings and reported similar results with learned positional embeddings; later models use other positional schemes. This induces a [bias](https://en.wikipedia.org/wiki/Inductive_bias) towards the order of the input sequence, so that, for example, the input sequence "[man bites dog](https://en.wikipedia.org/wiki/Man_bites_dog)" is processed differently from "dog bites man".

The positional encoding is defined as a function of type , where  is a positive even [integer](https://en.wikipedia.org/wiki/Integer). The full positional encoding defined in the original paper is:where .[\[1\]](https://en.wikipedia.org/wiki/Transformer_%28deep_learning%29#cite_note-2017_Attention_Is_All_You_Need-1)

Here,  denotes a sequence position and  indexes pairs of embedding dimensions.  controls the range of sinusoidal wavelengths; the original paper used .

The function is in a simpler form when written as a complex function of type where .

The main reason for using this positional encoding function is that using it, shifts are linear transformations:where  is the distance one wishes to shift. This allows the transformer to take any encoded position, and find the encoding of the position n-steps-ahead or n-steps-behind, by a matrix multiplication.

By taking a linear sum, any convolution can also be implemented as linear transformations:for any constants . This allows the transformer to take any encoded position and find a linear sum of the encoded locations of its neighbors. This sum of encoded positions, when fed into the attention mechanism, would create attention weights on its neighbors, much like what happens in a [convolutional neural network](https://en.wikipedia.org/wiki/Convolutional_neural_network) [language model](https://en.wikipedia.org/wiki/Language_model). In the author's words, "we hypothesized it would allow the model to easily learn to attend by relative position."

In typical implementations, all operations are done over the real numbers, not the complex numbers, but since [complex multiplication can be implemented as real 2-by-2 matrix multiplication](https://en.wikipedia.org/wiki/Complex_number#Matrix_representation_of_complex_numbers), this is a mere notational difference.

### Encoder–decoder (overview)

Like earlier [seq2seq](https://en.wikipedia.org/wiki/Seq2seq) models, the original transformer model used an **encoder–decoder** architecture. The encoder consists of encoding layers that process all the input tokens together one layer after another, while the decoder consists of decoding layers that iteratively process the encoder's output and the decoder's output tokens so far.

The purpose of each encoder layer is to create contextualized representations of the tokens, where each representation corresponds to a token that "mixes" information from other input tokens via self-attention mechanism. Each decoder layer contains two attention sublayers: (1) cross-attention for incorporating the output of encoder (contextualized input token representations), and (2) self-attention for "mixing" information among the input tokens to the decoder (i.e. the tokens generated so far during inference time).\[_[citation needed](https://en.wikipedia.org/wiki/Wikipedia:Citation_needed)_\]

Both the encoder and decoder layers have a [feed-forward neural network](https://en.wikipedia.org/wiki/Feedforward_neural_network) for additional processing of their outputs and contain residual connections and layer normalization steps. These feed-forward layers contain most of the parameters in a transformer model.\[_[citation needed](https://en.wikipedia.org/wiki/Wikipedia:Citation_needed)_\]

### Feedforward network

The feedforward network (FFN) modules in a transformer are 2-layered [multilayer perceptrons](https://en.wikipedia.org/wiki/Feedforward_neural_network):where  and  are weight matrices and  and  are bias vectors, and  is its activation function. The original transformer used [ReLU](https://en.wikipedia.org/wiki/Rectifier_%28neural_networks%29) activation.

The number of neurons in the middle layer is called _intermediate size_ (GPT),[\[46\]](https://en.wikipedia.org/wiki/Transformer_%28deep_learning%29#cite_note-48) _filter size_ (BERT),[\[28\]](https://en.wikipedia.org/wiki/Transformer_%28deep_learning%29#cite_note-:03-30) or _feedforward size_ (BERT).[\[28\]](https://en.wikipedia.org/wiki/Transformer_%28deep_learning%29#cite_note-:03-30) It is typically larger than the embedding size. For example, in both GPT-2 series and BERT series, the intermediate size of a model is 4 times its embedding size: .

### Scaled dot-product attention

Main article: Dot-product attention

#### Attention head

The attention mechanism used in the transformer architecture are scaled [dot-product](https://en.wikipedia.org/wiki/Dot_product) [attention](https://en.wikipedia.org/wiki/Attention_%28machine_learning%29) units. For each unit, the transformer model learns three weight matrices: the query weights , the key weights , and the value weights .

The module takes three sequences, a query sequence, a key sequence, and a value sequence. The query sequence is a sequence of length , and each entry is a vector of dimension . Similarly for the key and value sequences.

For each vector  in the query sequence, it is multiplied by a matrix  to produce a query vector . The matrix of all query vectors is the query matrix:Similarly, we construct the key matrix  and the value matrix .

The shapes of  depend on the input and head dimensions; these projection matrices need not be square.

Attention weights are calculated using the query and key vectors: the attention weight  from token  to token  is the [dot product](https://en.wikipedia.org/wiki/Dot_product) between  and . The attention weights are divided by the square root of the dimension of the key vectors, , which stabilizes gradients during training, and passed through a [softmax](https://en.wikipedia.org/wiki/Softmax_function) which normalizes the weights. The fact that  and  are different matrices allows attention to be non-symmetric: if token  attends to token  (i.e.  is large), this does not necessarily mean that token  will attend to token  (i.e.  could be small). The output of the attention unit for token  is the weighted sum of the value vectors of all tokens, weighted by , the attention from token  to each token.

The attention calculation for all tokens can be expressed as one large matrix calculation using the [softmax function](https://en.wikipedia.org/wiki/Softmax_function), which is useful for training due to computational matrix operation optimizations that quickly compute matrix operations. The matrices ,  and  are defined as the matrices where the th rows are vectors , , and  respectively. Then we can represent the attention as

where the softmax is applied over each of the rows of the matrix.

The number of dimensions in a query vector is _query size_  and similarly for the _key size_  and _value size_ . The output dimension of an attention head is its _head dimension_ . The attention mechanism requires the following three equalities to hold:but is otherwise unconstrained.

If the attention head is used in a self-attention fashion, then . If the attention head is used in a cross-attention fashion, then usually . It is theoretically possible for all three to be different, but that is rarely the case in practice.

#### Multihead attention

One set of  matrices is called an _attention head_, and each layer in a transformer model has multiple attention heads. While each attention head attends to the tokens that are relevant to each token, multiple attention heads allow the model to do this for different definitions of "relevance". Specifically, the query and key projection matrices,  and , which are involved in the attention score computation, defines the "relevance". Meanwhile, the value [projection matrix](https://en.wikipedia.org/wiki/Projection_matrix) , in combination with the part of the output projection matrix , determines how the attended tokens influence what information is passed to subsequent layers and ultimately the output logits. In addition, the scope of attention, or the range of token relationships captured by each attention head, can expand as tokens pass through successive layers. This allows the model to capture more complex and long-range dependencies in deeper layers. Analyses of some models have found attention heads that focus on patterns such as nearby words or syntactic relations; these patterns vary across heads and models.[\[47\]](https://en.wikipedia.org/wiki/Transformer_%28deep_learning%29#cite_note-49) The computations for each attention head can be performed in [parallel](https://en.wikipedia.org/wiki/Parallel_computing), which allows for fast processing. The outputs for the attention layer are concatenated to pass into the [feedforward neural network](https://en.wikipedia.org/wiki/Feedforward_neural_network) layers.

Concretely, let the multiple attention heads be indexed by , then we have where  contains the input representations to the attention layer (embeddings in the first layer and hidden states in later layers), and the matrices  are projection matrices for attention head , and  is a final projection matrix owned by the whole multihead attention module.

It is theoretically possible for each attention head to have a different head dimension , but that is rarely the case in practice.

As an example, in the smallest GPT-2 model, there are only self-attention mechanisms. It has the following dimensions:Since , its output projection matrix  is a square matrix.

#### Masked attention

Autoregressive decoders predict each token from earlier tokens. During training, causal self-attention can process all sequence positions in parallel while preventing position  from attending to later positions . During inference, the model generates tokens autoregressively. This mask is applied before softmax by adding a matrix  with  at masked positions and  elsewhere: The following matrix is commonly used in decoder self-attention modules, called "causal masking":

In words, it means that each token can pay attention to itself, and every token before it, but not any after it. A non-masked attention module can be thought of as a masked attention module where the mask has all entries zero. As an example of an uncommon use of mask matrix, the [XLNet](https://en.wikipedia.org/wiki/XLNet) considers all masks of the form , where  is a random [permutation matrix](https://en.wikipedia.org/wiki/Permutation_matrix).[\[48\]](https://en.wikipedia.org/wiki/Transformer_%28deep_learning%29#cite_note-50)

### Encoder

An encoder consists of an embedding layer, followed by multiple encoder layers.

Each encoder layer consists of two major components: a self-attention mechanism and a feed-forward layer. It takes an input as a sequence of input vectors, applies the self-attention mechanism, to produce an intermediate sequence of vectors, then applies the feed-forward layer for each vector individually. Schematically, we have:

where  stands for "feed-forward network". We can more succinctly write it aswith the implicit convention that the  is applied to each row of the matrix individually.

The encoder layers are stacked. The first encoder layer takes the sequence of input vectors from the embedding layer, producing a sequence of vectors. This sequence of vectors is processed by the second encoder, and so on. The output from the final encoder layer is then used by the decoder.

As the encoder processes the entire input all at once, every token can attend to every other token (all-to-all attention), so there is no need for causal masking.

### Decoder

A decoder consists of an embedding layer, followed by multiple decoder layers, followed by an un-embedding layer.

Each decoder consists of three major components: a causally masked self-attention mechanism, a cross-attention mechanism, and a feed-forward neural network. The decoder functions in a similar fashion to the encoder, but an additional attention mechanism is inserted which instead draws relevant information from the encodings generated by the encoders. This mechanism can also be called the _encoder–decoder attention_.[\[1\]](https://en.wikipedia.org/wiki/Transformer_%28deep_learning%29#cite_note-2017_Attention_Is_All_You_Need-1)\[_[non-primary source needed](https://en.wikipedia.org/wiki/Wikipedia:No_original_research#Primary,_secondary_and_tertiary_sources)_\] Like the first encoder, the first decoder takes positional information and embeddings of the output sequence as its input, rather than encodings. During training, target tokens are shifted right before being supplied to the decoder, and causal masking prevents each position from attending to later target tokens.[\[1\]](https://en.wikipedia.org/wiki/Transformer_%28deep_learning%29#cite_note-2017_Attention_Is_All_You_Need-1) This allows for [autoregressive](https://en.wikipedia.org/wiki/Autoregressive_model) text generation. For decoding, all-to-all attention is inappropriate, because a token cannot attend to tokens not yet generated. Thus, the self-attention module in the decoder is causally masked.

In contrast, the cross-attention mechanism attends to the output vectors of the encoder, which is computed before the decoder starts decoding. Consequently, there is no need for masking in the cross-attention mechanism.

Schematically, we have:where  is the matrix with rows being the output vectors from the encoder.

The last decoder is followed by a final un-embedding layer to produce the output probabilities over the vocabulary. Then, one of the tokens is sampled according to the probability, and the decoder can be run again to produce the next token, etc., autoregressively generating output text.

## Full transformer architecture

### Sublayers

Each encoder layer contains 2 sublayers: the self-attention and the feedforward network. Each decoder layer contains 3 sublayers: the causally masked self-attention, the cross-attention, and the feedforward network.

The original Transformer uses [residual connections](https://en.wikipedia.org/wiki/Residual_neural_network) and [layer normalization](https://en.wikipedia.org/wiki/Layer_normalization) (LayerNorm, or LN). Their placement and use vary across Transformer architectures.

The residual connections are introduced to avoid vanishing gradient issues and stabilize the training process. They can be expressed by , where  is a given component of the transformer. Adding the input  can preserve the input information and avoid issues when the gradient of  is close to zero.

Similarly to how the feedforward network modules are applied individually to each vector, the LayerNorm is also applied individually to each vector.

There are two common conventions in use: the _post-LN_ and the _pre-LN_ convention. In the post-LN convention, the output of each sublayer is where  is the function implemented by the sublayer itself.

In the pre-LN convention, the output of each sublayer isThe original 2017 transformer used the post-LN convention. It was difficult to train and required careful hyperparameter tuning and a "warm-up" in learning rate, where it starts small and gradually increases. The pre-LN convention, proposed several times in 2018,[\[49\]](https://en.wikipedia.org/wiki/Transformer_%28deep_learning%29#cite_note-51) was found to be easier to train, requiring no warm-up, leading to faster convergence.[\[36\]](https://en.wikipedia.org/wiki/Transformer_%28deep_learning%29#cite_note-auto1-38)

### Pseudocode

The following is the pseudocode for a standard pre-LN encoder–decoder transformer, adapted from _Formal Algorithms for Transformers_.[\[50\]](https://en.wikipedia.org/wiki/Transformer_%28deep_learning%29#cite_note-52)

```
input: Encoder input t_e
       Decoder input t_d
output: Array of probability distributions, with shape (decoder vocabulary size x length(decoder output sequence))

/* encoder */
z_e ← encoder.tokenizer(t_e)

for each t in 1:length(z_e) do
    z_e[t] ← encoder.embedding(z_e[t]) + encoder.positional_embedding(t)

for each l in 1:length(encoder.layers) do
    layer ← encoder.layers[l]

    /* first sublayer */
    z_e_copy ← copy(z_e)
    for each t in 1:length(z_e) do
        z_e[t] ← layer.layer_norm(z_e[t])
    z_e ← layer.multihead_attention(z_e, z_e, z_e)
    for each t in 1:length(z_e) do
        z_e[t] ← z_e[t] + z_e_copy[t]

    /* second sublayer */
    z_e_copy ← copy(z_e)
    for each t in 1:length(z_e) do
        z_e[t] ← layer.layer_norm(z_e[t])
    z_e ← layer.feedforward(z_e)
    for each t in 1:length(z_e) do
        z_e[t] ← z_e[t] + z_e_copy[t]

for each t in 1:length(z_e) do
    z_e[t] ← encoder.final_layer_norm(z_e[t])

/* decoder */
z_d ← decoder.tokenizer(t_d)

for each t in 1:length(z_d) do
    z_d[t] ← decoder.embedding(z_d[t]) + decoder.positional_embedding(t)

for each l in 1:length(decoder.layers) do
        layer ← decoder.layers[l]

        /* first sublayer */
        z_d_copy ← copy(z_d)
        for each t in 1:length(z_d) do
            z_d[t] ← layer.layer_norm(z_d[t])
        z_d ← layer.masked_multihead_attention(z_d, z_d, z_d)
        for each t in 1:length(z_d) do
            z_d[t] ← z_d[t] + z_d_copy[t]

        /* second sublayer */
        z_d_copy ← copy(z_d)
        for each t in 1:length(z_d) do
            z_d[t] ← layer.layer_norm(z_d[t])
        z_d ← layer.multihead_attention(z_d, z_e, z_e) 
       for each t in 1:length(z_d) do
           z_d[t] ← z_d[t] + z_d_copy[t]

        /* third sublayer */
        z_d_copy ← copy(z_d)
        for each t in 1:length(z_d) do
            z_d[t] ← layer.layer_norm(z_d[t])
        z_d ← layer.feedforward(z_d)
        for each t in 1:length(z_d) do
            z_d[t] ← z_d[t] + z_d_copy[t]

z_d ← decoder.final_layer_norm(z_d)

output_distributions ← []
for each t in 1:length(z_d) do
    output_distributions.append(decoder.unembed(z_d[t]))

return output_distributions
```

### Terminology

The transformer architecture, being modular, allows variations. Several common variations are described here.[\[41\]](https://en.wikipedia.org/wiki/Transformer_%28deep_learning%29#cite_note-Raffel_Shazeer_2020_Exploring_the_Limits-43)

An "encoder-only" Transformer maps an input sequence to contextualized representations. It is commonly used for text classification, retrieval, and representation learning. [BERT](https://en.wikipedia.org/wiki/BERT_%28language_model%29) is an example. Encoder-only models are also called "all-to-all" or "BERT-like" because their self-attention can generally use the full input sequence.

A "decoder-only" Transformer has causal self-attention and feed-forward layers, with no separate encoder or encoder–decoder cross-attention. It is commonly used for [text generation](https://en.wikipedia.org/wiki/Natural_language_generation) and [instruction following](https://en.wikipedia.org/wiki/Large_language_model#Instruction_tuning). The models in the [GPT series](https://en.wikipedia.org/wiki/Generative_pre-trained_transformer) and [Chinchilla series](https://en.wikipedia.org/wiki/Chinchilla_%28language_model%29) are examples. Such models are also called autoregressive or causal language models.

An "encoder–decoder" Transformer has an encoder that processes an input sequence and a decoder that generates an output sequence. In the original design, each decoder layer includes causal self-attention, cross-attention to encoder representations, and a feed-forward network; later models vary these details. The [T5 series](https://en.wikipedia.org/wiki/T5_%28language_model%29) is encoder–decoder.[\[41\]](https://en.wikipedia.org/wiki/Transformer_%28deep_learning%29#cite_note-Raffel_Shazeer_2020_Exploring_the_Limits-43)

A "prefixLM" (prefix language model) is a decoder-only architecture, but with prefix masking, which is different from causal masking. Specifically, it has mask of the form[\[41\]](https://en.wikipedia.org/wiki/Transformer_%28deep_learning%29#cite_note-Raffel_Shazeer_2020_Exploring_the_Limits-43): Figure 3 [\[51\]](https://en.wikipedia.org/wiki/Transformer_%28deep_learning%29#cite_note-53)where the block rows and columns correspond to prefix and continuation positions. Prefix tokens can attend to all prefix tokens; continuation tokens can attend to the prefix and earlier continuation tokens. This mask combines bidirectional attention within the prefix with causal attention over the continuation.[\[43\]](https://en.wikipedia.org/wiki/Transformer_%28deep_learning%29#cite_note-:4-45)

There are also mixed seq2seq models. For example, in 2020, Google Translate replaced the previous RNN-encoder–RNN-decoder model with a transformer-encoder–RNN-decoder model, as transformer-based decoders did not appear to significantly increase quality unlike the encoder, while the RNN decoder was much faster.[\[30\]](https://en.wikipedia.org/wiki/Transformer_%28deep_learning%29#cite_note-gtrans-32)

## Subsequent work

Many improvements have been added to the Transformer architecture. Transformer variants use different combinations of design choices, including [positional encodings](https://en.wikipedia.org/wiki/Transformer_%28deep_learning%29#Alternative_positional_encodings), [normalization methods](https://en.wikipedia.org/wiki/Transformer_%28deep_learning%29#Alternative_normalizations), and [feed-forward modules](https://en.wikipedia.org/wiki/Transformer_%28deep_learning%29#Alternative_feedforward_module).

### Alternative feedforward module

Main article: Gating mechanism

The original transformer's feedforward module is a standard linear-[ReLU](https://en.wikipedia.org/wiki/ReLU)-linear network. Other feedforward modules were developed. The [Llama series](https://en.wikipedia.org/wiki/Llama_%28language_model%29) and [PaLM](https://en.wikipedia.org/wiki/PaLM) used SwiGLU;[\[52\]](https://en.wikipedia.org/wiki/Transformer_%28deep_learning%29#cite_note-:14-54) both GPT-1 and BERT[\[28\]](https://en.wikipedia.org/wiki/Transformer_%28deep_learning%29#cite_note-:03-30) used GELU.[\[53\]](https://en.wikipedia.org/wiki/Transformer_%28deep_learning%29#cite_note-55)

Alternative activation functions are often used in combination with [Gated Linear Units](https://en.wikipedia.org/wiki/Gated_Linear_Unit) in the feedforward module.[\[52\]](https://en.wikipedia.org/wiki/Transformer_%28deep_learning%29#cite_note-:14-54)

### Alternative normalizations

Main article: Normalization (machine learning) § Transformers

The normalization used in the transformer can be different from LayerNorm. One example is [RMSNorm](https://en.wikipedia.org/wiki/RMSNorm)[\[54\]](https://en.wikipedia.org/wiki/Transformer_%28deep_learning%29#cite_note-56) which is used in the [Llama series](https://en.wikipedia.org/wiki/Llama_%28language_model%29). Other examples include ScaleNorm[\[55\]](https://en.wikipedia.org/wiki/Transformer_%28deep_learning%29#cite_note-:9-57) and FixNorm.[\[55\]](https://en.wikipedia.org/wiki/Transformer_%28deep_learning%29#cite_note-:9-57)

### Alternative positional encodings

Main article: Positional encoding

Transformers may use other positional encoding methods than sinusoidal.[\[56\]](https://en.wikipedia.org/wiki/Transformer_%28deep_learning%29#cite_note-58)

The original transformer paper reported using a learned positional encoding,[\[57\]](https://en.wikipedia.org/wiki/Transformer_%28deep_learning%29#cite_note-59) but finding it not superior to the sinusoidal one.[\[1\]](https://en.wikipedia.org/wiki/Transformer_%28deep_learning%29#cite_note-2017_Attention_Is_All_You_Need-1) Later,[\[58\]](https://en.wikipedia.org/wiki/Transformer_%28deep_learning%29#cite_note-60) found that causal masking itself provides enough signal to a transformer decoder that it can learn to implicitly perform absolute positional encoding without the positional encoding module.

### Efficient implementation

The transformer model has been implemented in standard deep learning [frameworks](https://en.wikipedia.org/wiki/Framework_%28computer_science%29) such as [TensorFlow](https://en.wikipedia.org/wiki/TensorFlow) and [PyTorch](https://en.wikipedia.org/wiki/PyTorch). _Transformers_ is a library produced by [Hugging Face](https://en.wikipedia.org/wiki/Hugging_Face) that supplies transformer-based architectures and pretrained models.[\[9\]](https://en.wikipedia.org/wiki/Transformer_%28deep_learning%29#cite_note-wolf2020-9)

#### KV caching

When an autoregressive transformer is used for inference, such as generating text, the query vector is different at each step, but the already-computed key and value vectors are always the same. The **KV caching** method saves the computed key and value vectors at each attention block, so that they are not recomputed at each new token. [PagedAttention](https://en.wikipedia.org/wiki/PagedAttention) applies [memory paging](https://en.wikipedia.org/wiki/Memory_paging) to KV caching.[\[59\]](https://en.wikipedia.org/wiki/Transformer_%28deep_learning%29#cite_note-61)[\[60\]](https://en.wikipedia.org/wiki/Transformer_%28deep_learning%29#cite_note-62)[\[61\]](https://en.wikipedia.org/wiki/Transformer_%28deep_learning%29#cite_note-63)

For repeated requests with the same prefix, an inference system may cache the prefix's key and value states and reuse them, provided the model and relevant settings match. This can reduce repeated computation; the cache consumes memory and may be invalidated when the prompt or model changes.

In general, when a user uses an autoregressive transformer to generate a continuation to a sequence of tokens, the model would first perform a forward-pass on this sequence, whereby the KV caches over this sequence are computed. This is called **prefilling**. After prefilling, the actual token generation is called **decoding**. [Hyperscalers](https://en.wikipedia.org/wiki/Hyperscale_computing) serving large Transformer models may use **disaggregated inference**, wherein prefilling and decoding are performed on separately specialized hardware.[\[62\]](https://en.wikipedia.org/wiki/Transformer_%28deep_learning%29#cite_note-64)

#### Continuous Batching

When using autoregressive transformer models, requests can have different input lengths and can finish generating at different times. Continuous batching adds new requests to batch and removes completed requests between decoding iterations instead of waiting for every request in a batch to finish. This can improve hardware utilization and throughput for concurrent workloads. Its effect on latency depends on the workload and scheduling policy.[\[63\]](https://en.wikipedia.org/wiki/Transformer_%28deep_learning%29#cite_note-65)

#### Quantization

Transformer models are often quantized for inference, meaning that weights, activations, or both are represented with lower-precision numerical formats than the floating point formats used during training. Quantization can reduce memory use and data transfer costs and can improve inference speed on hardware that supports low precision arithmetic. The trade off is that aggressive quantization can come at the cost of model accuracy or may need calibration and specialized quantization methods to perform well.[\[64\]](https://en.wikipedia.org/wiki/Transformer_%28deep_learning%29#cite_note-66)

#### FlashAttention

FlashAttention[\[65\]](https://en.wikipedia.org/wiki/Transformer_%28deep_learning%29#cite_note-Dao_Ermon_Fu_FlashAttention-67) is an exact attention algorithm that tiles the computation to reduce data movement between high-bandwidth memory and on-chip SRAM. It avoids materializing the full attention matrix, reducing memory traffic and often improving speed and memory use on supported GPUs.The [FlashAttention](https://en.wikipedia.org/wiki/FlashAttention) method is a [communication-avoiding algorithm](https://en.wikipedia.org/wiki/Communication-avoiding_algorithm) that fuses these operations into a single loop, increasing the [arithmetic intensity](https://en.wikipedia.org/wiki/Arithmetic_intensity). It is an [online algorithm](https://en.wikipedia.org/wiki/Online_algorithm) that computes the following quantities:[\[66\]](https://en.wikipedia.org/wiki/Transformer_%28deep_learning%29#cite_note-68)[\[65\]](https://en.wikipedia.org/wiki/Transformer_%28deep_learning%29#cite_note-Dao_Ermon_Fu_FlashAttention-67)and returns . In practice, FlashAttention operates over multiple queries and keys per loop iteration, in a similar way as [blocked matrix multiplication](https://en.wikipedia.org/wiki/Communication-avoiding_algorithm#Blocked_%28tiled%29_matrix_multiplication). If [backpropagation](https://en.wikipedia.org/wiki/Backpropagation) is needed, then the output vectors and the intermediate arrays  are cached, and during the backward pass, attention matrices are [rematerialized](https://en.wikipedia.org/wiki/Rematerialization) from these, making it a form of gradient checkpointing.

FlashAttention-2 improves parallelism and work partitioning, which can increase performance across supported sequence lengths.[\[67\]](https://en.wikipedia.org/wiki/Transformer_%28deep_learning%29#cite_note-69)

#### Multi-Query Attention

Multi-Query Attention (MQA) changes the Multihead Attention mechanism.[\[68\]](https://en.wikipedia.org/wiki/Transformer_%28deep_learning%29#cite_note-70) Whereas normally,

with Multi-Query Attention, there is just one , thus:

Sharing key and value projections across heads reduces the size of the KV cache and memory bandwidth required during autoregressive decoding; reported speed and quality effects depend on the model and task.

More generally, grouped-query attention (GQA) partitions attention heads into groups, each of which shares the key-value pair. MQA is GQA with one group, while standard Multihead Attention is GQA with the maximal number of groups.[\[69\]](https://en.wikipedia.org/wiki/Transformer_%28deep_learning%29#cite_note-71)

Multihead Latent Attention (MLA) is an alternative attention design that compresses key–value representations into a low-dimensional latent vector. The compressed representation reduces the KV-cache memory required during inference; MLA is distinct from MQA, which shares key and value heads across query heads.[\[70\]](https://en.wikipedia.org/wiki/Transformer_%28deep_learning%29#cite_note-:73-72)

#### Speculative decoding

Main article: Speculative decoding

Speculative decoding accelerates autoregressive generation by using a smaller draft model or another method to propose several tokens, then asking the target model to verify the proposal in a batched forward pass.[\[71\]](https://en.wikipedia.org/wiki/Transformer_%28deep_learning%29#cite_note-:2-73) The system accepts verified draft tokens and obtains a correction token when needed. With sampling, an acceptance and correction procedure can preserve the target model's output distribution.[\[72\]](https://en.wikipedia.org/wiki/Transformer_%28deep_learning%29#cite_note-74) The speedup depends on draft-model cost, acceptance rate, and hardware.

Multi-token prediction (MTP) is a training objective that adds prediction heads for multiple future tokens. It can provide additional training signal, and some systems use MTP predictions to support speculative decoding; MTP is not, by itself, a general inference method that produces an arbitrary number of future tokens in one pass.[\[73\]](https://en.wikipedia.org/wiki/Transformer_%28deep_learning%29#cite_note-75)[\[74\]](https://en.wikipedia.org/wiki/Transformer_%28deep_learning%29#cite_note-76)

### Sub-quadratic transformers

Training transformer-based architectures can be expensive, especially for long inputs.[\[75\]](https://en.wikipedia.org/wiki/Transformer_%28deep_learning%29#cite_note-reformer-77) Many methods have been developed to attempt to address the issue. In the image domain, Swin transformer is an efficient architecture that performs attention inside shifting windows.[\[76\]](https://en.wikipedia.org/wiki/Transformer_%28deep_learning%29#cite_note-78) In the audio domain, SepTr decouples the attention in time and frequency domains.[\[77\]](https://en.wikipedia.org/wiki/Transformer_%28deep_learning%29#cite_note-79) _Long Range Arena_ (2020)[\[78\]](https://en.wikipedia.org/wiki/Transformer_%28deep_learning%29#cite_note-80) is a standard benchmark for comparing the behavior of transformer architectures over long inputs.

The standard attention graph is either all-to-all or causal, both of which scales as  where  is the number of tokens in a sequence. In both cases, there are  pairs of tokens such that one influences the other within the attention block. By pruning the attention graph, the number of pairs of token influences can drop below . Such architectures are often referred to as _sparse_ attention, or sparse Transformers.

Sparse attention[\[79\]](https://en.wikipedia.org/wiki/Transformer_%28deep_learning%29#cite_note-81) uses sparse attention patterns to reduce computation for long sequences. BigBird combines local-window, random, and global attention links; with fixed block sizes, this pattern can scale linearly with sequence length.[\[80\]](https://en.wikipedia.org/wiki/Transformer_%28deep_learning%29#cite_note-82)

### Multimodality

Transformers can also be used/adapted for modalities (input or output) beyond just text, usually by finding a way to "tokenize" the modality.

Multimodal models can either be trained from scratch, or by finetuning. A 2022 study found that transformers pretrained only on natural language can be finetuned on only 0.03% of parameters and become competitive with [LSTMs](https://en.wikipedia.org/wiki/LSTMs) on a variety of logical and visual tasks, demonstrating [transfer learning](https://en.wikipedia.org/wiki/Transfer_learning).[\[81\]](https://en.wikipedia.org/wiki/Transformer_%28deep_learning%29#cite_note-83) LLaVA was a vision-language model composed of a language model (Vicuna-13B)[\[82\]](https://en.wikipedia.org/wiki/Transformer_%28deep_learning%29#cite_note-84) and a vision model ([ViT](https://en.wikipedia.org/wiki/Vision_transformer)-L/14), connected by a learned projection layer. In its first training stage, the projection layer was trained while the vision encoder and language model were frozen; in the later visual-instruction-tuning stage, the vision encoder remained frozen while the projection layer and language model were fine-tuned.[\[83\]](https://en.wikipedia.org/wiki/Transformer_%28deep_learning%29#cite_note-85)

[Vision transformers](https://en.wikipedia.org/wiki/Vision_transformer) adapt the transformer to computer vision by breaking down input images as a series of patches, turning them into vectors, and treating them like embedding vectors of tokens in a standard transformer.\[_[citation needed](https://en.wikipedia.org/wiki/Wikipedia:Citation_needed)_\]

[Conformer](https://en.wikipedia.org/wiki/Conformer_%28machine_learning%29?action=edit&redlink=1) combines self-attention with convolution modules to model both global and local patterns in speech.[\[84\]](https://en.wikipedia.org/wiki/Transformer_%28deep_learning%29#cite_note-86) [Whisper](https://en.wikipedia.org/wiki/Whisper_%28speech_recognition_system%29)[\[85\]](https://en.wikipedia.org/wiki/Transformer_%28deep_learning%29#cite_note-Radford_Kim_Xu_Brockman_p.-87) converts audio to log-Mel spectrogram features and processes them with convolutional layers and an encoder–decoder Transformer; it does not divide spectrograms into image-style patches.

[Perceivers](https://en.wikipedia.org/wiki/Perceiver)[\[86\]](https://en.wikipedia.org/wiki/Transformer_%28deep_learning%29#cite_note-perceiver2021-88)[\[87\]](https://en.wikipedia.org/wiki/Transformer_%28deep_learning%29#cite_note-jaegle2021b-89) are a variant of transformers designed for multimodality.

For image generation, notable architectures are [DALL-E 1](https://en.wikipedia.org/wiki/DALL-E) (2021), Parti (2022),[\[88\]](https://en.wikipedia.org/wiki/Transformer_%28deep_learning%29#cite_note-90) Phenaki (2023),[\[89\]](https://en.wikipedia.org/wiki/Transformer_%28deep_learning%29#cite_note-:13-91) and Muse (2023).[\[90\]](https://en.wikipedia.org/wiki/Transformer_%28deep_learning%29#cite_note-:12-92) Unlike later models, DALL-E is not a [diffusion model](https://en.wikipedia.org/wiki/Diffusion_model). Instead, it uses a decoder-only transformer that autoregressively generates a text, followed by the token representation of an image, which is then decoded by a [discrete variational autoencoder (dVAE)](https://en.wikipedia.org/wiki/Variational_autoencoder) into an image.[\[91\]](https://en.wikipedia.org/wiki/Transformer_%28deep_learning%29#cite_note-93) Parti is an encoder–decoder transformer, where the encoder processes a text prompt, and the decoder generates a token representation of an image.[\[92\]](https://en.wikipedia.org/wiki/Transformer_%28deep_learning%29#cite_note-94) Muse is an encoder-only transformer that is trained to predict masked image tokens from unmasked image tokens. During generation, all input tokens are masked, and the highest-confidence predictions are included for the next iteration, until all tokens are predicted.[\[90\]](https://en.wikipedia.org/wiki/Transformer_%28deep_learning%29#cite_note-:12-92) Phenaki is a text-to-video model. It is a bidirectional masked transformer conditioned on pre-computed text tokens. The generated tokens are then decoded to a video.[\[89\]](https://en.wikipedia.org/wiki/Transformer_%28deep_learning%29#cite_note-:13-91)

## Applications

The transformer has had great success in [natural language processing](https://en.wikipedia.org/wiki/Natural_language_processing) (NLP). Many [large language models](https://en.wikipedia.org/wiki/Large_language_model) such as [GPT-2](https://en.wikipedia.org/wiki/GPT-2), [GPT-3](https://en.wikipedia.org/wiki/GPT-3), [GPT-4](https://en.wikipedia.org/wiki/GPT-4), [Gemini](https://en.wikipedia.org/wiki/Gemini_%28chatbot%29), AlbertAGPT, [Claude](https://en.wikipedia.org/wiki/Claude_%28AI%29), [BERT](https://en.wikipedia.org/wiki/BERT_%28language_model%29), [Grok](https://en.wikipedia.org/wiki/Grok_%28chatbot%29), [XLNet](https://en.wikipedia.org/wiki/XLNet), [RoBERTa](https://en.wikipedia.org/wiki/BERT_%28language_model%29#RoBERTa) and [ChatGPT](https://en.wikipedia.org/wiki/ChatGPT) demonstrate the ability of transformers to perform a wide variety of NLP-related subtasks and their related real-world applications, including:

- machine translation
- time series prediction
- document summarization
- document generation
- named entity recognition (NER)[\[93\]](https://en.wikipedia.org/wiki/Transformer_%28deep_learning%29#cite_note-95)
- writing computer code based on requirements expressed in natural language.
- speech-to-text

Beyond traditional NLP, the transformer architecture has had success in other applications, such as:

- biological sequence analysis
- video understanding
- protein folding (such as AlphaFold)
- evaluating chess board positions. A transformer-based chess policy achieved an Elo rating of 2,895 in Lichess blitz games against human players without explicit search.[\[8\]](https://en.wikipedia.org/wiki/Transformer_%28deep_learning%29#cite_note-grandmaster-8)
- service function chain embedding[\[94\]](https://en.wikipedia.org/wiki/Transformer_%28deep_learning%29#cite_note-96)

## See also

- seq2seq – Family of machine learning approaches
- Circuit (neural network) – Interpretable computational sub-graphs within artificial neural networks
- Perceiver – Variant of Transformer designed for multimodal data
- Vision transformer – Machine learning model for vision processing
- Large language model – Type of machine learning model
- BERT (language model) – Series of language models developed by Google AI
- Generative pre-trained transformer – Type of large language model
- T5 (language model) – Series of large language models developed by Google AI

## Notes

1. [↑](https://en.wikipedia.org/wiki/Transformer_%28deep_learning%29#cite_ref-10) [Gated recurrent units](https://en.wikipedia.org/wiki/Gated_recurrent_units) (2014) further reduced its complexity.
2. [↑](https://en.wikipedia.org/wiki/Transformer_%28deep_learning%29#cite_ref-14) Some architectures, such as RWKV (Receptance Weighted Key Value) or state space models, avoid the issue.

## References

1. [1](https://en.wikipedia.org/wiki/Transformer_%28deep_learning%29#cite_ref-2017_Attention_Is_All_You_Need_1-0) [2](https://en.wikipedia.org/wiki/Transformer_%28deep_learning%29#cite_ref-2017_Attention_Is_All_You_Need_1-1) [3](https://en.wikipedia.org/wiki/Transformer_%28deep_learning%29#cite_ref-2017_Attention_Is_All_You_Need_1-2) [4](https://en.wikipedia.org/wiki/Transformer_%28deep_learning%29#cite_ref-2017_Attention_Is_All_You_Need_1-3) [5](https://en.wikipedia.org/wiki/Transformer_%28deep_learning%29#cite_ref-2017_Attention_Is_All_You_Need_1-4) [6](https://en.wikipedia.org/wiki/Transformer_%28deep_learning%29#cite_ref-2017_Attention_Is_All_You_Need_1-5) [7](https://en.wikipedia.org/wiki/Transformer_%28deep_learning%29#cite_ref-2017_Attention_Is_All_You_Need_1-6) [8](https://en.wikipedia.org/wiki/Transformer_%28deep_learning%29#cite_ref-2017_Attention_Is_All_You_Need_1-7) [9](https://en.wikipedia.org/wiki/Transformer_%28deep_learning%29#cite_ref-2017_Attention_Is_All_You_Need_1-8) [10](https://en.wikipedia.org/wiki/Transformer_%28deep_learning%29#cite_ref-2017_Attention_Is_All_You_Need_1-9) [Vaswani, Ashish](https://en.wikipedia.org/wiki/Ashish_Vaswani); Shazeer, Noam; Parmar, Niki; Uszkoreit, Jakob; Jones, Llion; [Gomez, Aidan N](https://en.wikipedia.org/wiki/Aidan_Gomez); Kaiser, Łukasz; Polosukhin, Illia (2017). ["Attention is All You Need"](https://web.archive.org/web/20240221141113/https://proceedings.neurips.cc/paper/2017/file/3f5ee243547dee91fbd053c1c4a845aa-Paper.pdf) ( (PDF)). _31st Conference on Neural Information Processing Systems (NIPS 2017), 4-9 December 2017, Long Beach, CA, USA_. Vol. 30. Curran Associates, Inc. [arXiv](https://en.wikipedia.org/wiki/ArXiv_%28identifier%29):[1706.03762](https://arxiv.org/abs/1706.03762). [ISBN](https://en.wikipedia.org/wiki/ISBN_%28identifier%29) [978-1-5108-6096-4](https://en.wikipedia.org/wiki/Special:BookSources/978-1-5108-6096-4). Archived from [the original](https://proceedings.neurips.cc/paper/2017/file/3f5ee243547dee91fbd053c1c4a845aa-Paper.pdf) on 2024-02-21. Retrieved 2023-10-31.
2. [1](https://en.wikipedia.org/wiki/Transformer_%28deep_learning%29#cite_ref-lstm1997_2-0) [2](https://en.wikipedia.org/wiki/Transformer_%28deep_learning%29#cite_ref-lstm1997_2-1) [Hochreiter, Sepp](https://en.wikipedia.org/wiki/Sepp_Hochreiter); [Schmidhuber, Jürgen](https://en.wikipedia.org/wiki/Jürgen_Schmidhuber) (November 1997). "Long Short-Term Memory". _Neural Computation_. **9** (8): 1735–1780. [doi](https://en.wikipedia.org/wiki/Doi_%28identifier%29):[10.1162/neco.1997.9.8.1735](https://doi.org/10.1162%2Fneco.1997.9.8.1735). [PMID](https://en.wikipedia.org/wiki/PMID_%28identifier%29) [9377276](https://pubmed.ncbi.nlm.nih.gov/9377276).
3. [1](https://en.wikipedia.org/wiki/Transformer_%28deep_learning%29#cite_ref-inventors_3-0) [2](https://en.wikipedia.org/wiki/Transformer_%28deep_learning%29#cite_ref-inventors_3-1) Bahdanau; Cho, Kyunghyun; Bengio, Yoshua (September 1, 2014). "Neural Machine Translation by Jointly Learning to Align and Translate". [arXiv](https://en.wikipedia.org/wiki/ArXiv_%28identifier%29):[1409.0473](https://arxiv.org/abs/1409.0473) \[[cs.CL](https://arxiv.org/archive/cs.CL)\].
4. [↑](https://en.wikipedia.org/wiki/Transformer_%28deep_learning%29#cite_ref-inventconfirm_4-0) Luong, Minh-Thang; Pham, Hieu; Manning, Christopher D. (August 17, 2015). "Effective Approaches to Attention-based Neural Machine Translation". [arXiv](https://en.wikipedia.org/wiki/ArXiv_%28identifier%29):[1508.04025](https://arxiv.org/abs/1508.04025) \[[cs.CL](https://arxiv.org/archive/cs.CL)\].
5. [↑](https://en.wikipedia.org/wiki/Transformer_%28deep_learning%29#cite_ref-5) Parisotto, Emilio; Song, Francis; Rae, Jack; Pascanu, Razvan; Gulcehre, Caglar; Jayakumar, Siddhant; Jaderberg, Max; Kaufman, Raphaël Lopez; Clark, Aidan; Noury, Seb; Botvinick, Matthew; Heess, Nicolas; Hadsell, Raia (2020-11-21). ["Stabilizing Transformers for Reinforcement Learning"](https://proceedings.mlr.press/v119/parisotto20a.html). _Proceedings of the 37th International Conference on Machine Learning_. PMLR: 7487–7498. [Archived](https://web.archive.org/web/20240809053144/https://proceedings.mlr.press/v119/parisotto20a.html) from the original on 2024-08-09. Retrieved 2024-08-09.
6. [↑](https://en.wikipedia.org/wiki/Transformer_%28deep_learning%29#cite_ref-Robust_Speech_Recognition_via_Large-Scale_Weak_Supervision_6-0) Radford, Alec; Jong Wook Kim; Xu, Tao; Brockman, Greg; McLeavey, Christine; Sutskever, Ilya (2022). "Robust Speech Recognition via Large-Scale Weak Supervision". [arXiv](https://en.wikipedia.org/wiki/ArXiv_%28identifier%29):[2212.04356](https://arxiv.org/abs/2212.04356) \[[eess.AS](https://arxiv.org/archive/eess.AS)\].
7. [↑](https://en.wikipedia.org/wiki/Transformer_%28deep_learning%29#cite_ref-7) Monastirsky, Maxim; Azulay, Osher; Sintov, Avishai (February 2023). "Learning to Throw With a Handful of Samples Using Decision Transformers". _IEEE Robotics and Automation Letters_. **8** (2): 576–583. [Bibcode](https://en.wikipedia.org/wiki/Bibcode_%28identifier%29):[2023IRAL....8..576M](https://scixplorer.org/abs/2023IRAL....8..576M). [doi](https://en.wikipedia.org/wiki/Doi_%28identifier%29):[10.1109/LRA.2022.3229266](https://doi.org/10.1109%2FLRA.2022.3229266).
8. [1](https://en.wikipedia.org/wiki/Transformer_%28deep_learning%29#cite_ref-grandmaster_8-0) [2](https://en.wikipedia.org/wiki/Transformer_%28deep_learning%29#cite_ref-grandmaster_8-1) Ruoss, Anian; Delétang, Grégoire; Medapati, Sourabh; Grau-Moya, Jordi; Wenliang, Li; Catt, Elliot; Reid, John; Genewein, Tim (2024-02-07). "Grandmaster-Level Chess Without Search". [arXiv](https://en.wikipedia.org/wiki/ArXiv_%28identifier%29):[2402.04494v1](https://arxiv.org/abs/2402.04494v1) \[[cs.LG](https://arxiv.org/archive/cs.LG)\].
9. [1](https://en.wikipedia.org/wiki/Transformer_%28deep_learning%29#cite_ref-wolf2020_9-0) [2](https://en.wikipedia.org/wiki/Transformer_%28deep_learning%29#cite_ref-wolf2020_9-1) Wolf, Thomas; Debut, Lysandre; Sanh, Victor; Chaumond, Julien; Delangue, Clement; Moi, Anthony; Cistac, Pierric; Rault, Tim; Louf, Remi; Funtowicz, Morgan; Davison, Joe; Shleifer, Sam; von Platen, Patrick; Ma, Clara; Jernite, Yacine; Plu, Julien; Xu, Canwen; Le Scao, Teven; Gugger, Sylvain; Drame, Mariama; Lhoest, Quentin; Rush, Alexander (2020). "Transformers: State-of-the-Art Natural Language Processing". _Proceedings of the 2020 Conference on Empirical Methods in Natural Language Processing: System Demonstrations_. pp. 38–45. [doi](https://en.wikipedia.org/wiki/Doi_%28identifier%29):[10.18653/v1/2020.emnlp-demos.6](https://doi.org/10.18653%2Fv1%2F2020.emnlp-demos.6).
10. [↑](https://en.wikipedia.org/wiki/Transformer_%28deep_learning%29#cite_ref-11) Feldman, J; Ballard, D (September 1982). "Connectionist models and their properties". _Cognitive Science_. **6** (3): 205–254. [doi](https://en.wikipedia.org/wiki/Doi_%28identifier%29):[10.1016/S0364-0213(82)80001-3](https://doi.org/10.1016%2FS0364-0213%2882%2980001-3).
11. [↑](https://en.wikipedia.org/wiki/Transformer_%28deep_learning%29#cite_ref-PDP_12-0) Rumelhart, David E.; Hinton, Geoffrey E.; McClelland, James L. (1986). "Interactive Processes in Speech Perception". _Parallel Distributed Processing_. [doi](https://en.wikipedia.org/wiki/Doi_%28identifier%29):[10.7551/mitpress/5236.003.0005](https://doi.org/10.7551%2Fmitpress%2F5236.003.0005). [ISBN](https://en.wikipedia.org/wiki/ISBN_%28identifier%29) [978-0-262-29140-8](https://en.wikipedia.org/wiki/Special:BookSources/978-0-262-29140-8).
12. [↑](https://en.wikipedia.org/wiki/Transformer_%28deep_learning%29#cite_ref-13) Giles, C. Lee; Maxwell, Tom (December 1987). "Learning, invariance, and generalization in high-order neural networks". _Applied Optics_. **26** (23): 4972–4978. [doi](https://en.wikipedia.org/wiki/Doi_%28identifier%29):[10.1364/AO.26.004972](https://doi.org/10.1364%2FAO.26.004972). [PMID](https://en.wikipedia.org/wiki/PMID_%28identifier%29) [20523475](https://pubmed.ncbi.nlm.nih.gov/20523475).
13. [1](https://en.wikipedia.org/wiki/Transformer_%28deep_learning%29#cite_ref-:22_15-0) [2](https://en.wikipedia.org/wiki/Transformer_%28deep_learning%29#cite_ref-:22_15-1) Cho, Kyunghyun; van Merriënboer, Bart; Gulcehre, Caglar; Bahdanau, Dzmitry; Bougares, Fethi; Schwenk, Holger; Bengio, Yoshua (October 2014). ["Learning Phrase Representations using RNN Encoder–Decoder for Statistical Machine Translation"](https://aclanthology.org/D14-1179). In Moschitti, Alessandro; Pang, Bo; Daelemans, Walter (eds.). _Proceedings of the 2014 Conference on Empirical Methods in Natural Language Processing (EMNLP)_. Doha, Qatar: Association for Computational Linguistics. pp. 1724–1734. [arXiv](https://en.wikipedia.org/wiki/ArXiv_%28identifier%29):[1406.1078](https://arxiv.org/abs/1406.1078). [doi](https://en.wikipedia.org/wiki/Doi_%28identifier%29):[10.3115/v1/D14-1179](https://doi.org/10.3115%2Fv1%2FD14-1179). [Archived](https://web.archive.org/web/20240906214240/https://aclanthology.org/D14-1179/) from the original on 2024-09-06. Retrieved 2024-08-09.
14. [1](https://en.wikipedia.org/wiki/Transformer_%28deep_learning%29#cite_ref-sequence_16-0) [2](https://en.wikipedia.org/wiki/Transformer_%28deep_learning%29#cite_ref-sequence_16-1) Sutskever, Ilya; Vinyals, Oriol; Le, Quoc Viet (14 Dec 2014). "Sequence to sequence learning with neural networks". [arXiv](https://en.wikipedia.org/wiki/ArXiv_%28identifier%29):[1409.3215](https://arxiv.org/abs/1409.3215) \[[cs.CL](https://arxiv.org/archive/cs.CL)\]. \[first version posted to arXiv on 10 Sep 2014\]
15. [↑](https://en.wikipedia.org/wiki/Transformer_%28deep_learning%29#cite_ref-MyUser_Arxiv.org_May_18_2016c_17-0) Chung, Junyoung; Gulcehre, Caglar; Cho, KyungHyun; Bengio, Yoshua (2014). "Empirical Evaluation of Gated Recurrent Neural Networks on Sequence Modeling". [arXiv](https://en.wikipedia.org/wiki/ArXiv_%28identifier%29):[1412.3555](https://arxiv.org/abs/1412.3555) \[[cs.NE](https://arxiv.org/archive/cs.NE)\].
16. [↑](https://en.wikipedia.org/wiki/Transformer_%28deep_learning%29#cite_ref-gruber_jockisch_18-0) Gruber, Nicole; Jockisch, Alfred (30 June 2020). ["Are GRU Cells More Specific and LSTM Cells More Sensitive in Motive Classification of Text?"](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC7861254). _Frontiers in Artificial Intelligence_. **3** 40. [doi](https://en.wikipedia.org/wiki/Doi_%28identifier%29):[10.3389/frai.2020.00040](https://doi.org/10.3389%2Ffrai.2020.00040). [PMC](https://en.wikipedia.org/wiki/PMC_%28identifier%29) [7861254](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC7861254). [PMID](https://en.wikipedia.org/wiki/PMID_%28identifier%29) [33733157](https://pubmed.ncbi.nlm.nih.gov/33733157).
17. [↑](https://en.wikipedia.org/wiki/Transformer_%28deep_learning%29#cite_ref-19) Sutskever, Ilya; Vinyals, Oriol; Le, Quoc V (2014). ["Sequence to Sequence Learning with Neural Networks"](https://web.archive.org/web/20250127094117/https://proceedings.neurips.cc/paper/2014/hash/a14ac55a4f27472c5d894ec1c3c743d2-Abstract.html). _Advances in Neural Information Processing Systems_. **27**. Curran Associates, Inc. [arXiv](https://en.wikipedia.org/wiki/ArXiv_%28identifier%29):[1409.3215](https://arxiv.org/abs/1409.3215). Archived from [the original](https://proceedings.neurips.cc/paper/2014/hash/a14ac55a4f27472c5d894ec1c3c743d2-Abstract.html) on 2025-01-27. Retrieved 2024-07-23.
18. [↑](https://en.wikipedia.org/wiki/Transformer_%28deep_learning%29#cite_ref-20) Luong, Minh-Thang; Pham, Hieu; Manning, Christopher D. (2015). "Effective Approaches to Attention-based Neural Machine Translation". [arXiv](https://en.wikipedia.org/wiki/ArXiv_%28identifier%29):[1508.04025](https://arxiv.org/abs/1508.04025) \[[cs.CL](https://arxiv.org/archive/cs.CL)\].
19. [↑](https://en.wikipedia.org/wiki/Transformer_%28deep_learning%29#cite_ref-Y4moj_21-0) Wu, Yonghui; et al. (2016-09-01). "Google's Neural Machine Translation System: Bridging the Gap between Human and Machine Translation". [arXiv](https://en.wikipedia.org/wiki/ArXiv_%28identifier%29):[1609.08144](https://arxiv.org/abs/1609.08144) \[[cs.CL](https://arxiv.org/archive/cs.CL)\].
20. [↑](https://en.wikipedia.org/wiki/Transformer_%28deep_learning%29#cite_ref-UJDu8_22-0) Lewis-Kraus, Gideon (2016-12-14). ["The Great A.I. Awakening"](https://web.archive.org/web/20230524052626/https://www.nytimes.com/2016/12/14/magazine/the-great-ai-awakening.html). _The New York Times_. Archived from [the original](https://www.nytimes.com/2016/12/14/magazine/the-great-ai-awakening.html) on 24 May 2023. Retrieved 2023-06-22.
21. [↑](https://en.wikipedia.org/wiki/Transformer_%28deep_learning%29#cite_ref-23) Parikh, Ankur P.; Täckström, Oscar; Das, Dipanjan; Uszkoreit, Jakob (2016-09-25). "A Decomposable Attention Model for Natural Language Inference". [arXiv](https://en.wikipedia.org/wiki/ArXiv_%28identifier%29):[1606.01933](https://arxiv.org/abs/1606.01933) \[[cs.CL](https://arxiv.org/archive/cs.CL)\].
22. [1](https://en.wikipedia.org/wiki/Transformer_%28deep_learning%29#cite_ref-:11_24-0) [2](https://en.wikipedia.org/wiki/Transformer_%28deep_learning%29#cite_ref-:11_24-1) Levy, Steven. ["8 Google Employees Invented Modern AI. Here's the Inside Story"](https://www.wired.com/story/eight-google-employees-invented-modern-ai-transformers-paper/). _Wired_. [Archived](https://web.archive.org/web/20240320101528/https://www.wired.com/story/eight-google-employees-invented-modern-ai-transformers-paper/) from the original on 20 Mar 2024. Retrieved 2024-08-06.
23. [↑](https://en.wikipedia.org/wiki/Transformer_%28deep_learning%29#cite_ref-25) Cheng, Jianpeng; Dong, Li; Lapata, Mirella (November 2016). ["Long Short-Term Memory-Networks for Machine Reading"](https://aclanthology.org/D16-1053/). In Su, Jian; Duh, Kevin; Carreras, Xavier (eds.). _Proceedings of the 2016 Conference on Empirical Methods in Natural Language Processing_. Austin, Texas: Association for Computational Linguistics. pp. 551–561. [doi](https://en.wikipedia.org/wiki/Doi_%28identifier%29):[10.18653/v1/D16-1053](https://doi.org/10.18653%2Fv1%2FD16-1053). [Archived](https://web.archive.org/web/20240827143929/https://aclanthology.org/D16-1053/) from the original on 2024-08-27. Retrieved 2024-08-27.
24. [↑](https://en.wikipedia.org/wiki/Transformer_%28deep_learning%29#cite_ref-26) Peng, Bo; Alcaide, Eric; Anthony, Quentin; Albalak, Alon; Arcadinho, Samuel; Biderman, Stella; Cao, Huanqi; Cheng, Xin; Chung, Michael (2023-12-10). "RWKV: Reinventing RNNs for the transformer Era". [arXiv](https://en.wikipedia.org/wiki/ArXiv_%28identifier%29):[2305.13048](https://arxiv.org/abs/2305.13048) \[[cs.CL](https://arxiv.org/archive/cs.CL)\].
25. [↑](https://en.wikipedia.org/wiki/Transformer_%28deep_learning%29#cite_ref-27) Marche, Stephen (2024-08-23). ["Was Linguistic A.I. Created by Accident?"](https://www.newyorker.com/science/annals-of-artificial-intelligence/was-linguistic-ai-created-by-accident). _The New Yorker_. Retrieved 2024-08-27.
26. [↑](https://en.wikipedia.org/wiki/Transformer_%28deep_learning%29#cite_ref-28) Vaswani, Ashish; Bengio, Samy; Brevdo, Eugene; Chollet, Francois; Gomez, Aidan; Gouws, Stephan; Jones, Llion; Kaiser, Łukasz; Kalchbrenner, Nal; Parmar, Niki; Sepassi, Ryan; Shazeer, Noam; Uszkoreit, Jakob (March 2018). Cherry, Colin; Neubig, Graham (eds.). ["Tensor2Tensor for Neural Machine Translation"](https://aclanthology.org/W18-1819/). _Proceedings of the 13th Conference of the Association for Machine Translation in the Americas (Volume 1: Research Track)_. Boston, MA: Association for Machine Translation in the Americas: 193–199. [Archived](https://web.archive.org/web/20260429230143/https://aclanthology.org/W18-1819/) from the original on 2026-04-29. Retrieved 2026-03-31.
27. [↑](https://en.wikipedia.org/wiki/Transformer_%28deep_learning%29#cite_ref-29) Kaiser, Łukasz (2017-06-19). ["Accelerating Deep Learning Research with the Tensor2Tensor Library"](https://research.google/blog/accelerating-deep-learning-research-with-the-tensor2tensor-library/). _Google Research Blog_. [Archived](https://web.archive.org/web/20260415200010/https://research.google/blog/accelerating-deep-learning-research-with-the-tensor2tensor-library/) from the original on 2026-04-15. Retrieved 2026-03-31.
28. [1](https://en.wikipedia.org/wiki/Transformer_%28deep_learning%29#cite_ref-:03_30-0) [2](https://en.wikipedia.org/wiki/Transformer_%28deep_learning%29#cite_ref-:03_30-1) [3](https://en.wikipedia.org/wiki/Transformer_%28deep_learning%29#cite_ref-:03_30-2) [4](https://en.wikipedia.org/wiki/Transformer_%28deep_learning%29#cite_ref-:03_30-3) [5](https://en.wikipedia.org/wiki/Transformer_%28deep_learning%29#cite_ref-:03_30-4) Devlin, Jacob; Chang, Ming-Wei; Lee, Kenton; Toutanova, Kristina (11 October 2018). "BERT: Pre-training of Deep Bidirectional Transformers for Language Understanding". [arXiv](https://en.wikipedia.org/wiki/ArXiv_%28identifier%29):[1810.04805v2](https://arxiv.org/abs/1810.04805v2) \[[cs.CL](https://arxiv.org/archive/cs.CL)\].
29. [↑](https://en.wikipedia.org/wiki/Transformer_%28deep_learning%29#cite_ref-31) ["Google: BERT now used on almost every English query"](https://searchengineland.com/google-bert-used-on-almost-every-english-query-342193). _Search Engine Land_. 2020-10-15. [Archived](https://web.archive.org/web/20220506220519/https://searchengineland.com/google-bert-used-on-almost-every-english-query-342193) from the original on 2022-05-06. Retrieved 2020-11-24.
30. [1](https://en.wikipedia.org/wiki/Transformer_%28deep_learning%29#cite_ref-gtrans_32-0) [2](https://en.wikipedia.org/wiki/Transformer_%28deep_learning%29#cite_ref-gtrans_32-1) Caswell, Isaac; Liang, Bowen (June 8, 2020). ["Recent Advances in Google Translate"](https://research.google/blog/recent-advances-in-google-translate/). _Google Research_. [Archived](https://web.archive.org/web/20240704042433/https://research.google/blog/recent-advances-in-google-translate/) from the original on 4 Jul 2024. Retrieved 2024-08-07.
31. [↑](https://en.wikipedia.org/wiki/Transformer_%28deep_learning%29#cite_ref-33) ["The inside story of how ChatGPT was built from the people who made it"](https://www.technologyreview.com/2023/03/03/1069311/inside-story-oral-history-how-chatgpt-built-openai/). _MIT Technology Review_. [Archived](https://web.archive.org/web/20230303093219/https://www.technologyreview.com/2023/03/03/1069311/inside-story-oral-history-how-chatgpt-built-openai/) from the original on 2023-03-03. Retrieved 2024-08-06.
32. [↑](https://en.wikipedia.org/wiki/Transformer_%28deep_learning%29#cite_ref-34) ["Introducing ChatGPT"](https://openai.com/index/chatgpt/). _OpenAI_. 2022-11-30. [Archived](https://web.archive.org/web/20260405004654/https://openai.com/index/chatgpt/) from the original on 2026-04-05. Retrieved 2026-05-16.
33. [↑](https://en.wikipedia.org/wiki/Transformer_%28deep_learning%29#cite_ref-35) Deign, Jason (December 6, 2024). ["How ChatGPT changed… well, almost everything"](https://newsroom.cisco.com/c/r/newsroom/en/us/a/y2024/m12/how-chatgpt-changed-well-almost-everything.html). _Cisco Newsroom_. Retrieved 2026-10-22.
34. [↑](https://en.wikipedia.org/wiki/Transformer_%28deep_learning%29#cite_ref-36) Kaiser, Lukasz; Gomez, Aidan N.; Shazeer, Noam; Vaswani, Ashish; Parmar, Niki; Jones, Llion; Uszkoreit, Jakob (2017-06-16). "One Model To Learn Them All". [arXiv](https://en.wikipedia.org/wiki/ArXiv_%28identifier%29):[1706.05137v1](https://arxiv.org/abs/1706.05137v1) \[[cs.LG](https://arxiv.org/archive/cs.LG)\].
35. [↑](https://en.wikipedia.org/wiki/Transformer_%28deep_learning%29#cite_ref-37) Liu, Zhuang; Mao, Hanzi; Wu, Chao-Yuan; Feichtenhofer, Christoph; Darrell, Trevor; Xie, Saining (2022). [_A ConvNet for the 2020s_](https://openaccess.thecvf.com/content/CVPR2022/html/Liu_A_ConvNet_for_the_2020s_CVPR_2022_paper.html). Conference on Computer Vision and Pattern Recognition ([CVPR](https://en.wikipedia.org/wiki/CVPR)). pp. 11976–11986.
36. [1](https://en.wikipedia.org/wiki/Transformer_%28deep_learning%29#cite_ref-auto1_38-0) [2](https://en.wikipedia.org/wiki/Transformer_%28deep_learning%29#cite_ref-auto1_38-1) Xiong, Ruibin; Yang, Yunchang; He, Di; Zheng, Kai; Zheng, Shuxin; Xing, Chen; Zhang, Huishuai; Lan, Yanyan; Wang, Liwei; Liu, Tie-Yan (2020-06-29). "On Layer Normalization in the Transformer Architecture". [arXiv](https://en.wikipedia.org/wiki/ArXiv_%28identifier%29):[2002.04745](https://arxiv.org/abs/2002.04745) \[[cs.LG](https://arxiv.org/archive/cs.LG)\].
37. [↑](https://en.wikipedia.org/wiki/Transformer_%28deep_learning%29#cite_ref-39) Vaswani, Ashish; Shazeer, Noam; Parmar, Niki; Uszkoreit, Jakob; Jones, Llion; Gomez, Aidan N; Kaiser, Ł ukasz; Polosukhin, Illia (2017). ["Attention is All you Need"](https://papers.neurips.cc/paper_files/paper/2017/hash/3f5ee243547dee91fbd053c1c4a845aa-Abstract.html). _Advances in Neural Information Processing Systems_. **30**. Curran Associates, Inc.
38. [↑](https://en.wikipedia.org/wiki/Transformer_%28deep_learning%29#cite_ref-40) Narayanan, Deepak; Harlap, Aaron; Phanishayee, Amar; Seshadri, Vivek; Devanur, Nikhil R.; Ganger, Gregory R.; Gibbons, Phillip B.; Zaharia, Matei (2019). "PipeDream: Generalized pipeline parallelism for DNN training". _Proceedings of the 27th ACM Symposium on Operating Systems Principles_. pp. 1–15. [doi](https://en.wikipedia.org/wiki/Doi_%28identifier%29):[10.1145/3341301.3359646](https://doi.org/10.1145%2F3341301.3359646). [ISBN](https://en.wikipedia.org/wiki/ISBN_%28identifier%29) [978-1-4503-6873-5](https://en.wikipedia.org/wiki/Special:BookSources/978-1-4503-6873-5).
39. [1](https://en.wikipedia.org/wiki/Transformer_%28deep_learning%29#cite_ref-:8_41-0) [2](https://en.wikipedia.org/wiki/Transformer_%28deep_learning%29#cite_ref-:8_41-1) [3](https://en.wikipedia.org/wiki/Transformer_%28deep_learning%29#cite_ref-:8_41-2) ["Causal language modeling"](https://huggingface.co/docs/transformers/tasks/language_modeling). _huggingface.co_. [Archived](https://web.archive.org/web/20231010083913/https://huggingface.co/docs/transformers/tasks/language_modeling) from the original on 2023-10-10. Retrieved 2023-10-05.
40. [1](https://en.wikipedia.org/wiki/Transformer_%28deep_learning%29#cite_ref-:5_42-0) [2](https://en.wikipedia.org/wiki/Transformer_%28deep_learning%29#cite_ref-:5_42-1) [3](https://en.wikipedia.org/wiki/Transformer_%28deep_learning%29#cite_ref-:5_42-2) ["Masked language modeling"](https://huggingface.co/docs/transformers/tasks/masked_language_modeling). _huggingface.co_. [Archived](https://web.archive.org/web/20231010083915/https://huggingface.co/docs/transformers/tasks/masked_language_modeling) from the original on 2023-10-10. Retrieved 2023-10-05.
41. [1](https://en.wikipedia.org/wiki/Transformer_%28deep_learning%29#cite_ref-Raffel_Shazeer_2020_Exploring_the_Limits_43-0) [2](https://en.wikipedia.org/wiki/Transformer_%28deep_learning%29#cite_ref-Raffel_Shazeer_2020_Exploring_the_Limits_43-1) [3](https://en.wikipedia.org/wiki/Transformer_%28deep_learning%29#cite_ref-Raffel_Shazeer_2020_Exploring_the_Limits_43-2) [4](https://en.wikipedia.org/wiki/Transformer_%28deep_learning%29#cite_ref-Raffel_Shazeer_2020_Exploring_the_Limits_43-3) [5](https://en.wikipedia.org/wiki/Transformer_%28deep_learning%29#cite_ref-Raffel_Shazeer_2020_Exploring_the_Limits_43-4) Raffel, Colin; Shazeer, Noam; Roberts, Adam; Lee, Katherine; Narang, Sharan; Matena, Michael; Zhou, Yanqi; Li, Wei; Liu, Peter J. (2020). ["Exploring the Limits of Transfer Learning with a Unified Text-to-Text Transformer"](https://www.jmlr.org/papers/v21/20-074.html). _Journal of Machine Learning Research_. **21** (140): 1–67. [Archived](https://web.archive.org/web/20260410072046/https://jmlr.org/papers/v21/20-074.html) from the original on 2026-04-10. Retrieved 2026-04-18.
42. [↑](https://en.wikipedia.org/wiki/Transformer_%28deep_learning%29#cite_ref-44) Raffel, Colin; Shazeer, Noam; Roberts, Adam; Lee, Katherine; Narang, Sharan; Matena, Michael; Zhou, Yanqi; Li, Wei; Liu, Peter J. (2019). "Exploring the Limits of Transfer Learning with a Unified Text-to-Text Transformer". [arXiv](https://en.wikipedia.org/wiki/ArXiv_%28identifier%29):[1910.10683](https://arxiv.org/abs/1910.10683) \[[cs.LG](https://arxiv.org/archive/cs.LG)\].
43. [1](https://en.wikipedia.org/wiki/Transformer_%28deep_learning%29#cite_ref-:4_45-0) [2](https://en.wikipedia.org/wiki/Transformer_%28deep_learning%29#cite_ref-:4_45-1) Tay, Yi; Dehghani, Mostafa; Tran, Vinh Q.; Garcia, Xavier; Wei, Jason; Wang, Xuezhi; Chung, Hyung Won; Shakeri, Siamak; Bahri, Dara (2023-02-28). "UL2: Unifying Language Learning Paradigms". [arXiv](https://en.wikipedia.org/wiki/ArXiv_%28identifier%29):[2205.05131](https://arxiv.org/abs/2205.05131) \[[cs.CL](https://arxiv.org/archive/cs.CL)\].
44. [↑](https://en.wikipedia.org/wiki/Transformer_%28deep_learning%29#cite_ref-46) Sennrich, Rico; Haddow, Barry; Birch, Alexandra (2016). "Neural Machine Translation of Rare Words with Subword Units". _Proceedings of the 54th Annual Meeting of the Association for Computational Linguistics_. [doi](https://en.wikipedia.org/wiki/Doi_%28identifier%29):[10.18653/v1/P16-1162](https://doi.org/10.18653%2Fv1%2FP16-1162).
45. [↑](https://en.wikipedia.org/wiki/Transformer_%28deep_learning%29#cite_ref-47) Kudo, Taku (2018). "Subword Regularization: Improving Neural Network Translation Models with Multiple Subword Candidates". _Proceedings of the 56th Annual Meeting of the Association for Computational Linguistics_. [doi](https://en.wikipedia.org/wiki/Doi_%28identifier%29):[10.18653/v1/D18-2012](https://doi.org/10.18653%2Fv1%2FD18-2012).
46. [↑](https://en.wikipedia.org/wiki/Transformer_%28deep_learning%29#cite_ref-48) Team, Keras. ["Keras documentation: GPT2Backbone model"](https://keras.io/api/keras_nlp/models/gpt2/gpt2_backbone/). _keras.io_. [Archived](https://web.archive.org/web/20240808085714/https://keras.io/api/keras_nlp/models/gpt2/gpt2_backbone/) from the original on 2024-08-08. Retrieved 2024-08-08.
47. [↑](https://en.wikipedia.org/wiki/Transformer_%28deep_learning%29#cite_ref-49) Clark, Kevin; Khandelwal, Urvashi; Levy, Omer; Manning, Christopher D. (August 2019). ["What Does BERT Look at? An Analysis of BERT's Attention"](https://www.aclweb.org/anthology/W19-4828). _Proceedings of the 2019 ACL Workshop BlackboxNLP: Analyzing and Interpreting Neural Networks for NLP_. Florence, Italy: Association for Computational Linguistics: 276–286. [arXiv](https://en.wikipedia.org/wiki/ArXiv_%28identifier%29):[1906.04341](https://arxiv.org/abs/1906.04341). [doi](https://en.wikipedia.org/wiki/Doi_%28identifier%29):[10.18653/v1/W19-4828](https://doi.org/10.18653%2Fv1%2FW19-4828). [Archived](https://web.archive.org/web/20201021211357/https://www.aclweb.org/anthology/W19-4828/) from the original on 2020-10-21. Retrieved 2020-05-20.
48. [↑](https://en.wikipedia.org/wiki/Transformer_%28deep_learning%29#cite_ref-50) Yang, Zhilin; Dai, Zihang; Yang, Yiming; Carbonell, Jaime; Salakhutdinov, Russ R; Le, Quoc V (2019). ["XLNet: Generalized Autoregressive Pretraining for Language Understanding"](https://proceedings.neurips.cc/paper/2019/hash/dc6a7e655d7e5840e66733e9ee67cc69-Abstract.html). _Advances in Neural Information Processing Systems_. **32**. Curran Associates, Inc. [arXiv](https://en.wikipedia.org/wiki/ArXiv_%28identifier%29):[1906.08237](https://arxiv.org/abs/1906.08237). [Archived](https://web.archive.org/web/20240809053521/https://proceedings.neurips.cc/paper/2019/hash/dc6a7e655d7e5840e66733e9ee67cc69-Abstract.html) from the original on 2024-08-09. Retrieved 2024-08-09.
49. [↑](https://en.wikipedia.org/wiki/Transformer_%28deep_learning%29#cite_ref-51) Wang, Qiang; Li, Bei; Xiao, Tong; Zhu, Jingbo; Li, Changliang; Wong, Derek F.; Chao, Lidia S. (2019-06-04). "Learning Deep Transformer Models for Machine Translation". [arXiv](https://en.wikipedia.org/wiki/ArXiv_%28identifier%29):[1906.01787](https://arxiv.org/abs/1906.01787) \[[cs.CL](https://arxiv.org/archive/cs.CL)\].
50. [↑](https://en.wikipedia.org/wiki/Transformer_%28deep_learning%29#cite_ref-52) Phuong, Mary; Hutter, Marcus (2022-07-19). "Formal Algorithms for Transformers". [arXiv](https://en.wikipedia.org/wiki/ArXiv_%28identifier%29):[2207.09238](https://arxiv.org/abs/2207.09238) \[[cs.LG](https://arxiv.org/archive/cs.LG)\].
51. [↑](https://en.wikipedia.org/wiki/Transformer_%28deep_learning%29#cite_ref-53) Dong, Li; Yang, Nan; Wang, Wenhui; Wei, Furu; Liu, Xiaodong; Wang, Yu; Gao, Jianfeng; Zhou, Ming; Hon, Hsiao-Wuen (2019). ["Unified Language Model Pre-training for Natural Language Understanding and Generation"](https://proceedings.neurips.cc/paper_files/paper/2019/hash/c20bb2d9a50d5ac1f713f8b34d9aac5a-Abstract.html). _Advances in Neural Information Processing Systems_. **32**. Curran Associates, Inc.
52. [1](https://en.wikipedia.org/wiki/Transformer_%28deep_learning%29#cite_ref-:14_54-0) [2](https://en.wikipedia.org/wiki/Transformer_%28deep_learning%29#cite_ref-:14_54-1) Shazeer, Noam (2020-02-01). "GLU Variants Improve Transformer". [arXiv](https://en.wikipedia.org/wiki/ArXiv_%28identifier%29):[2002.05202](https://arxiv.org/abs/2002.05202) \[[cs.LG](https://arxiv.org/archive/cs.LG)\].
53. [↑](https://en.wikipedia.org/wiki/Transformer_%28deep_learning%29#cite_ref-55) Hendrycks, Dan; Gimpel, Kevin (2016-06-27). "Gaussian Error Linear Units (GELUs)". [arXiv](https://en.wikipedia.org/wiki/ArXiv_%28identifier%29):[1606.08415v5](https://arxiv.org/abs/1606.08415v5) \[[cs.LG](https://arxiv.org/archive/cs.LG)\].
54. [↑](https://en.wikipedia.org/wiki/Transformer_%28deep_learning%29#cite_ref-56) Zhang, Biao; Sennrich, Rico (2019). ["Root Mean Square Layer Normalization"](https://proceedings.neurips.cc/paper/2019/hash/1e8a19426224ca89e83cef47f1e7f53b-Abstract.html). _Advances in Neural Information Processing Systems_. **32**. Curran Associates, Inc. [arXiv](https://en.wikipedia.org/wiki/ArXiv_%28identifier%29):[1910.07467](https://arxiv.org/abs/1910.07467). [Archived](https://web.archive.org/web/20240917113737/https://proceedings.neurips.cc/paper/2019/hash/1e8a19426224ca89e83cef47f1e7f53b-Abstract.html) from the original on 2024-09-17. Retrieved 2024-08-09.
55. [1](https://en.wikipedia.org/wiki/Transformer_%28deep_learning%29#cite_ref-:9_57-0) [2](https://en.wikipedia.org/wiki/Transformer_%28deep_learning%29#cite_ref-:9_57-1) Nguyen, Toan Q.; Salazar, Julian (2019-11-02). Niehues, Jan; Cattoni, Rolando; Stüker, Sebastian; Negri, Matteo; Turchi, Marco; Ha, Thanh-Le; Salesky, Elizabeth; Sanabria, Ramon; Barrault, Loic (eds.). ["Transformers without Tears: Improving the Normalization of Self-Attention"](https://aclanthology.org/2019.iwslt-1.17). _Proceedings of the 16th International Conference on Spoken Language Translation_. Hong Kong: Association for Computational Linguistics. [arXiv](https://en.wikipedia.org/wiki/ArXiv_%28identifier%29):[1910.05895](https://arxiv.org/abs/1910.05895). [doi](https://en.wikipedia.org/wiki/Doi_%28identifier%29):[10.5281/zenodo.3525484](https://doi.org/10.5281%2Fzenodo.3525484). [Archived](https://web.archive.org/web/20240809185028/https://aclanthology.org/2019.iwslt-1.17/) from the original on 2024-08-09. Retrieved 2024-08-09.
56. [↑](https://en.wikipedia.org/wiki/Transformer_%28deep_learning%29#cite_ref-58) Dufter, Philipp; Schmitt, Martin; Schütze, Hinrich (September 2022). ["Position Information in Transformers: An Overview"](https://doi.org/10.1162%2Fcoli_a_00445). _Computational Linguistics_. **48** (3): 733–763. [arXiv](https://en.wikipedia.org/wiki/ArXiv_%28identifier%29):[2102.11090](https://arxiv.org/abs/2102.11090). [doi](https://en.wikipedia.org/wiki/Doi_%28identifier%29):[10.1162/coli_a_00445](https://doi.org/10.1162%2Fcoli_a_00445).
57. [↑](https://en.wikipedia.org/wiki/Transformer_%28deep_learning%29#cite_ref-59) Gehring, Jonas; Auli, Michael; Grangier, David; Yarats, Denis; Dauphin, Yann N. (2017-07-17). ["Convolutional Sequence to Sequence Learning"](https://proceedings.mlr.press/v70/gehring17a.html). _Proceedings of the 34th International Conference on Machine Learning_. PMLR: 1243–1252. [Archived](https://web.archive.org/web/20240809184100/https://proceedings.mlr.press/v70/gehring17a.html) from the original on 2024-08-09. Retrieved 2024-08-09.
58. [↑](https://en.wikipedia.org/wiki/Transformer_%28deep_learning%29#cite_ref-60) Haviv, Adi; Ram, Ori; Press, Ofir; Izsak, Peter; Levy, Omer (2022-12-05). "Transformer Language Models without Positional Encodings Still Learn Positional Information". [arXiv](https://en.wikipedia.org/wiki/ArXiv_%28identifier%29):[2203.16634](https://arxiv.org/abs/2203.16634) \[[cs.CL](https://arxiv.org/archive/cs.CL)\].
59. [↑](https://en.wikipedia.org/wiki/Transformer_%28deep_learning%29#cite_ref-61) Kwon, Woosuk; Li, Zhuohan; Zhuang, Siyuan; Sheng, Ying; Zheng, Lianmin; Yu, Cody Hao; Gonzalez, Joseph; Zhang, Hao; Stoica, Ion (2023). "Efficient Memory Management for Large Language Model Serving with PagedAttention". _Proceedings of the 29th Symposium on Operating Systems Principles_. pp. 611–626. [doi](https://en.wikipedia.org/wiki/Doi_%28identifier%29):[10.1145/3600006.3613165](https://doi.org/10.1145%2F3600006.3613165). [ISBN](https://en.wikipedia.org/wiki/ISBN_%28identifier%29) [979-8-4007-0229-7](https://en.wikipedia.org/wiki/Special:BookSources/979-8-4007-0229-7).
60. [↑](https://en.wikipedia.org/wiki/Transformer_%28deep_learning%29#cite_ref-62) ["vllm-project/vllm"](https://github.com/vllm-project/vllm). vLLM. 2024-06-20. [Archived](https://web.archive.org/web/20240618204642/https://github.com/vllm-project/vllm) from the original on 2024-06-18. Retrieved 2024-06-20.
61. [↑](https://en.wikipedia.org/wiki/Transformer_%28deep_learning%29#cite_ref-63) Zhuohan Li, Woosuk Kwon; Zhuang, Siyuan; Sheng, Ying; Zheng, Lianmin; Yu, Cody; Gonzalez, Joey; Zhang, Hao; Stoica, Ion (2023-06-20). ["vLLM: Easy, Fast, and Cheap LLM Serving with PagedAttention"](https://blog.vllm.ai/2023/06/20/vllm.html). _vLLM Blog_. [Archived](https://web.archive.org/web/20240620205208/https://blog.vllm.ai/2023/06/20/vllm.html) from the original on 2024-06-20. Retrieved 2024-06-20.
62. [↑](https://en.wikipedia.org/wiki/Transformer_%28deep_learning%29#cite_ref-64) Hu, Cunchen; Huang, Heyang; Xu, Liangliang; Chen, Xusheng; Xu, Jiang; Chen, Shuang; Feng, Hao; Wang, Chenxi; Wang, Sa (2024-01-20). "Inference without Interference: Disaggregate LLM Inference for Mixed Downstream Workloads". [arXiv](https://en.wikipedia.org/wiki/ArXiv_%28identifier%29):[2401.11181](https://arxiv.org/abs/2401.11181) \[[cs.DC](https://arxiv.org/archive/cs.DC)\].
63. [↑](https://en.wikipedia.org/wiki/Transformer_%28deep_learning%29#cite_ref-65) Yu, Gyeong-In; Jeong, Joo Seong; Kim, Geon-Woo; Kim, Soojeong; Chun, Byung-Gon (2022). [_Orca: A Distributed Serving System for Transformer-Based Generative Models_](https://www.usenix.org/conference/osdi22/presentation/yu). pp. 521–538. [ISBN](https://en.wikipedia.org/wiki/ISBN_%28identifier%29) [978-1-939133-28-1](https://en.wikipedia.org/wiki/Special:BookSources/978-1-939133-28-1).
64. [↑](https://en.wikipedia.org/wiki/Transformer_%28deep_learning%29#cite_ref-66) Dettmers, Tim; Lewis, Mike; Belkada, Younes; Zettlemoyer, Luke (2022-08-15). "LLM.int8(): 8-bit Matrix Multiplication for Transformers at Scale". [arXiv](https://en.wikipedia.org/wiki/ArXiv_%28identifier%29):[2208.07339v2](https://arxiv.org/abs/2208.07339v2) \[[cs.LG](https://arxiv.org/archive/cs.LG)\].
65. [1](https://en.wikipedia.org/wiki/Transformer_%28deep_learning%29#cite_ref-Dao_Ermon_Fu_FlashAttention_67-0) [2](https://en.wikipedia.org/wiki/Transformer_%28deep_learning%29#cite_ref-Dao_Ermon_Fu_FlashAttention_67-1) Dao, Tri; Ermon, Stefano; Fu, Dan; Ré, Christopher; Rudra, Atri (2022). "FlashAttention: Fast and Memory-Efficient Exact Attention with IO-Awareness". _Advances in Neural Information Processing Systems 35_. pp. 16344–16359. [arXiv](https://en.wikipedia.org/wiki/ArXiv_%28identifier%29):[2205.14135](https://arxiv.org/abs/2205.14135). [doi](https://en.wikipedia.org/wiki/Doi_%28identifier%29):[10.52202/068431-1189](https://doi.org/10.52202%2F068431-1189). [ISBN](https://en.wikipedia.org/wiki/ISBN_%28identifier%29) [978-1-7138-7108-8](https://en.wikipedia.org/wiki/Special:BookSources/978-1-7138-7108-8).
66. [↑](https://en.wikipedia.org/wiki/Transformer_%28deep_learning%29#cite_ref-68) Milakov, Maxim; Gimelshein, Natalia (2018). "Online normalizer calculation for softmax". [arXiv](https://en.wikipedia.org/wiki/ArXiv_%28identifier%29):[1805.02867](https://arxiv.org/abs/1805.02867) \[[cs.PF](https://arxiv.org/archive/cs.PF)\].
67. [↑](https://en.wikipedia.org/wiki/Transformer_%28deep_learning%29#cite_ref-69) ["FlashAttention-2: Faster Attention with Better Parallelism and Work Partitioning"](https://crfm.stanford.edu/2023/07/17/flash2.html). _crfm.stanford.edu_. [Archived](https://web.archive.org/web/20230718103613/https://crfm.stanford.edu/2023/07/17/flash2.html) from the original on 2023-07-18. Retrieved 2023-07-18.
68. [↑](https://en.wikipedia.org/wiki/Transformer_%28deep_learning%29#cite_ref-70) Chowdhery, Aakanksha; Narang, Sharan; Devlin, Jacob; Bosma, Maarten; Mishra, Gaurav; Roberts, Adam; Barham, Paul; Chung, Hyung Won; Sutton, Charles; Gehrmann, Sebastian; Schuh, Parker; Shi, Kensen; Tsvyashchenko, Sasha; Maynez, Joshua; Rao, Abhishek (2022-04-01). "PaLM: Scaling Language Modeling with Pathways". [arXiv](https://en.wikipedia.org/wiki/ArXiv_%28identifier%29):[2204.02311](https://arxiv.org/abs/2204.02311) \[[cs.CL](https://arxiv.org/archive/cs.CL)\].
69. [↑](https://en.wikipedia.org/wiki/Transformer_%28deep_learning%29#cite_ref-71) Ainslie, Joshua; Lee-Thorp, James; de Jong, Michiel; Zemlyanskiy, Yury; Lebrón, Federico; Sanghai, Sumit (2023-12-23). "GQA: Training Generalized Multi-Query Transformer Models from Multi-Head Checkpoints". [arXiv](https://en.wikipedia.org/wiki/ArXiv_%28identifier%29):[2305.13245](https://arxiv.org/abs/2305.13245) \[[cs.CL](https://arxiv.org/archive/cs.CL)\].
70. [1](https://en.wikipedia.org/wiki/Transformer_%28deep_learning%29#cite_ref-:73_72-0) [2](https://en.wikipedia.org/wiki/Transformer_%28deep_learning%29#cite_ref-:73_72-1) DeepSeek-AI; Liu, Aixin; Feng, Bei; Wang, Bin; Wang, Bingxuan; Liu, Bo; Zhao, Chenggang; Dengr, Chengqi; Ruan, Chong (19 June 2024). "DeepSeek-V2: A Strong, Economical, and Efficient Mixture-of-Experts Language Model". [arXiv](https://en.wikipedia.org/wiki/ArXiv_%28identifier%29):[2405.04434](https://arxiv.org/abs/2405.04434) \[[cs.CL](https://arxiv.org/archive/cs.CL)\]..
71. [↑](https://en.wikipedia.org/wiki/Transformer_%28deep_learning%29#cite_ref-:2_73-0) Leviathan, Yaniv; Kalman, Matan; Matias, Yossi (2023-05-18). "Fast Inference from Transformers via Speculative Decoding". [arXiv](https://en.wikipedia.org/wiki/ArXiv_%28identifier%29):[2211.17192](https://arxiv.org/abs/2211.17192) \[[cs.LG](https://arxiv.org/archive/cs.LG)\].
72. [↑](https://en.wikipedia.org/wiki/Transformer_%28deep_learning%29#cite_ref-74) Chen, Charlie; Borgeaud, Sebastian; Irving, Geoffrey; Lespiau, Jean-Baptiste; Sifre, Laurent; Jumper, John (2023-02-02). "Accelerating Large Language Model Decoding with Speculative Sampling". [arXiv](https://en.wikipedia.org/wiki/ArXiv_%28identifier%29):[2302.01318](https://arxiv.org/abs/2302.01318) \[[cs.CL](https://arxiv.org/archive/cs.CL)\].
73. [↑](https://en.wikipedia.org/wiki/Transformer_%28deep_learning%29#cite_ref-75) Gloeckle, Fabian; Badr Youbi Idrissi; Rozière, Baptiste; Lopez-Paz, David; Synnaeve, Gabriel (2024). "Better & Faster Large Language Models via Multi-token Prediction". [arXiv](https://en.wikipedia.org/wiki/ArXiv_%28identifier%29):[2404.19737](https://arxiv.org/abs/2404.19737) \[[cs.CL](https://arxiv.org/archive/cs.CL)\].
74. [↑](https://en.wikipedia.org/wiki/Transformer_%28deep_learning%29#cite_ref-76) DeepSeek-AI; et al. (2024). "DeepSeek-V3 Technical Report". [arXiv](https://en.wikipedia.org/wiki/ArXiv_%28identifier%29):[2412.19437](https://arxiv.org/abs/2412.19437) \[[cs.CL](https://arxiv.org/archive/cs.CL)\].
75. [↑](https://en.wikipedia.org/wiki/Transformer_%28deep_learning%29#cite_ref-reformer_77-0) Kitaev, Nikita; Kaiser, Łukasz; Levskaya, Anselm (2020). "Reformer: The Efficient Transformer". [arXiv](https://en.wikipedia.org/wiki/ArXiv_%28identifier%29):[2001.04451](https://arxiv.org/abs/2001.04451) \[[cs.LG](https://arxiv.org/archive/cs.LG)\].
76. [↑](https://en.wikipedia.org/wiki/Transformer_%28deep_learning%29#cite_ref-78) Liu, Ze; Lin, Yutong; Cao, Yue; Hu, Han; Wei, Yixuan; Zhang, Zheng; Lin, Stephen; Guo, Baining (2021). "Swin Transformer: Hierarchical Vision Transformer using Shifted Windows". _2021 IEEE/CVF International Conference on Computer Vision (ICCV)_. IEEE. pp. 9992–10002. [arXiv](https://en.wikipedia.org/wiki/ArXiv_%28identifier%29):[2103.14030](https://arxiv.org/abs/2103.14030). [doi](https://en.wikipedia.org/wiki/Doi_%28identifier%29):[10.1109/ICCV48922.2021.00986](https://doi.org/10.1109%2FICCV48922.2021.00986). [ISBN](https://en.wikipedia.org/wiki/ISBN_%28identifier%29) [978-1-6654-2812-5](https://en.wikipedia.org/wiki/Special:BookSources/978-1-6654-2812-5).
77. [↑](https://en.wikipedia.org/wiki/Transformer_%28deep_learning%29#cite_ref-79) Ristea, Nicolaea Catalin; Ionescu, Radu Tudor; Khan, Fahad Shahbaz (2022-09-18). ["SepTr: Separable Transformer for Audio Spectrogram Processing"](https://www.isca-archive.org/interspeech_2022/ristea22_interspeech.html). _Interspeech_. ISCA: 4103–4107. [arXiv](https://en.wikipedia.org/wiki/ArXiv_%28identifier%29):[2203.09581](https://arxiv.org/abs/2203.09581). [doi](https://en.wikipedia.org/wiki/Doi_%28identifier%29):[10.21437/Interspeech.2022-249](https://doi.org/10.21437%2FInterspeech.2022-249).
78. [↑](https://en.wikipedia.org/wiki/Transformer_%28deep_learning%29#cite_ref-80) Tay, Yi; Dehghani, Mostafa; Abnar, Samira; Shen, Yikang; Bahri, Dara; Pham, Philip; Rao, Jinfeng; Yang, Liu; Ruder, Sebastian; Metzler, Donald (2020-11-08). "Long Range Arena: A Benchmark for Efficient Transformers". [arXiv](https://en.wikipedia.org/wiki/ArXiv_%28identifier%29):[2011.04006](https://arxiv.org/abs/2011.04006) \[[cs.LG](https://arxiv.org/archive/cs.LG)\].
79. [↑](https://en.wikipedia.org/wiki/Transformer_%28deep_learning%29#cite_ref-81) Child, Rewon; Gray, Scott; Radford, Alec; Sutskever, Ilya (2019-04-23). "Generating Long Sequences with Sparse Transformers". [arXiv](https://en.wikipedia.org/wiki/ArXiv_%28identifier%29):[1904.10509](https://arxiv.org/abs/1904.10509) \[[cs.LG](https://arxiv.org/archive/cs.LG)\].
80. [↑](https://en.wikipedia.org/wiki/Transformer_%28deep_learning%29#cite_ref-82) Zaheer, Manzil; Gupta, Guru; Kale, Shankar; Kumar, Yash; Contractor, Danish; Rathod, Vishwas; Re, Christopher (2020-10-06). "Big Bird: Transformers for Longer Sequences". [arXiv](https://en.wikipedia.org/wiki/ArXiv_%28identifier%29):[2007.14062](https://arxiv.org/abs/2007.14062) \[[cs.CL](https://arxiv.org/archive/cs.CL)\].
81. [↑](https://en.wikipedia.org/wiki/Transformer_%28deep_learning%29#cite_ref-83) Lu, Kevin; Grover, Aditya; Abbeel, Pieter; Mordatch, Igor (2022). "Frozen Pretrained Transformers as Universal Computation Engines". _Proceedings of the AAAI Conference on Artificial Intelligence_. **36** (7): 7628–7636. [doi](https://en.wikipedia.org/wiki/Doi_%28identifier%29):[10.1609/aaai.v36i7.20729](https://doi.org/10.1609%2Faaai.v36i7.20729).
82. [↑](https://en.wikipedia.org/wiki/Transformer_%28deep_learning%29#cite_ref-84) ["Vicuna: An Open-Source Chatbot Impressing GPT-4 with 90%* ChatGPT Quality | LMSYS Org"](https://lmsys.org/blog/2023-03-30-vicuna). _lmsys.org_. 30 March 2023. [Archived](https://web.archive.org/web/20240812055843/https://lmsys.org/blog/2023-03-30-vicuna/) from the original on 2024-08-12. Retrieved 2024-08-11.
83. [↑](https://en.wikipedia.org/wiki/Transformer_%28deep_learning%29#cite_ref-85) Liu, Haotian; Li, Chunyuan; Wu, Qingyang; Lee, Yong Jae (2023-12-15). ["Visual Instruction Tuning"](https://proceedings.neurips.cc/paper_files/paper/2023/hash/6dcf277ea32ce3288914faf369fe6de0-Abstract-Conference.html). _Advances in Neural Information Processing Systems_. Vol. 36. pp. 34892–34916. [doi](https://en.wikipedia.org/wiki/Doi_%28identifier%29):[10.52202/075280-1516](https://doi.org/10.52202%2F075280-1516). [ISBN](https://en.wikipedia.org/wiki/ISBN_%28identifier%29) [978-1-7138-9911-2](https://en.wikipedia.org/wiki/Special:BookSources/978-1-7138-9911-2). [Archived](https://web.archive.org/web/20240926183648/https://proceedings.neurips.cc//paper_files/paper/2023/hash/6dcf277ea32ce3288914faf369fe6de0-Abstract-Conference.html) from the original on 2024-09-26. Retrieved 2024-08-11.
84. [↑](https://en.wikipedia.org/wiki/Transformer_%28deep_learning%29#cite_ref-86) "Conformer: Convolution-augmented Transformer for Speech Recognition". [arXiv](https://en.wikipedia.org/wiki/ArXiv_%28identifier%29):[2005.08100](https://arxiv.org/abs/2005.08100) \[[cs.CL](https://arxiv.org/archive/cs.CL)\]. A bot will complete this citation soon. [Click here to jump the queue](https://citations.toolforge.org/process_page.php?page=Transformer_%28deep_learning%29&edit=template&slow=1)
85. [↑](https://en.wikipedia.org/wiki/Transformer_%28deep_learning%29#cite_ref-Radford_Kim_Xu_Brockman_p._87-0) Radford, Alec; Kim, Jong Wook; Xu, Tao; Brockman, Greg; McLeavey, Christine; Sutskever, Ilya (2022). "Robust Speech Recognition via Large-Scale Weak Supervision". [arXiv](https://en.wikipedia.org/wiki/ArXiv_%28identifier%29):[2212.04356](https://arxiv.org/abs/2212.04356) \[[eess.AS](https://arxiv.org/archive/eess.AS)\].
86. [↑](https://en.wikipedia.org/wiki/Transformer_%28deep_learning%29#cite_ref-perceiver2021_88-0) Jaegle, Andrew; Gimeno, Felix; Brock, Andrew; Zisserman, Andrew; Vinyals, Oriol; Carreira, Joao (2021-06-22). "Perceiver: General Perception with Iterative Attention". [arXiv](https://en.wikipedia.org/wiki/ArXiv_%28identifier%29):[2103.03206](https://arxiv.org/abs/2103.03206) \[[cs.CV](https://arxiv.org/archive/cs.CV)\].
87. [↑](https://en.wikipedia.org/wiki/Transformer_%28deep_learning%29#cite_ref-jaegle2021b_89-0) Jaegle, Andrew; Borgeaud, Sebastian; Alayrac, Jean-Baptiste; Doersch, Carl; Ionescu, Catalin; Ding, David; Koppula, Skanda; Zoran, Daniel; Brock, Andrew; Shelhamer, Evan; Hénaff, Olivier (2021-08-02). "Perceiver IO: A General Architecture for Structured Inputs & Outputs". [arXiv](https://en.wikipedia.org/wiki/ArXiv_%28identifier%29):[2107.14795](https://arxiv.org/abs/2107.14795) \[[cs.LG](https://arxiv.org/archive/cs.LG)\].
88. [↑](https://en.wikipedia.org/wiki/Transformer_%28deep_learning%29#cite_ref-90) ["Parti: Pathways Autoregressive Text-to-Image Model"](https://sites.research.google/parti/). _sites.research.google_. [Archived](https://web.archive.org/web/20240810094406/https://sites.research.google/parti/) from the original on 2024-08-10. Retrieved 2024-08-09.
89. [1](https://en.wikipedia.org/wiki/Transformer_%28deep_learning%29#cite_ref-:13_91-0) [2](https://en.wikipedia.org/wiki/Transformer_%28deep_learning%29#cite_ref-:13_91-1) Villegas, Ruben; Babaeizadeh, Mohammad; Kindermans, Pieter-Jan; Moraldo, Hernan; Zhang, Han; Saffar, Mohammad Taghi; Castro, Santiago; Kunze, Julius; Erhan, Dumitru (2022-09-29). "Phenaki: Variable Length Video Generation from Open Domain Textual Descriptions". [arXiv](https://en.wikipedia.org/wiki/ArXiv_%28identifier%29):[2210.02399](https://arxiv.org/abs/2210.02399) \[[cs.CV](https://arxiv.org/archive/cs.CV)\].
90. [1](https://en.wikipedia.org/wiki/Transformer_%28deep_learning%29#cite_ref-:12_92-0) [2](https://en.wikipedia.org/wiki/Transformer_%28deep_learning%29#cite_ref-:12_92-1) Chang, Huiwen; Zhang, Han; Barber, Jarred; Maschinot, A. J.; Lezama, Jose; Jiang, Lu; [Yang, Ming-Hsuan](https://en.wikipedia.org/wiki/Ming-Hsuan_Yang); Murphy, Kevin; Freeman, William T. (2023-01-02). "Muse: Text-To-Image Generation via Masked Generative Transformers". [arXiv](https://en.wikipedia.org/wiki/ArXiv_%28identifier%29):[2301.00704](https://arxiv.org/abs/2301.00704) \[[cs.CV](https://arxiv.org/archive/cs.CV)\].
91. [↑](https://en.wikipedia.org/wiki/Transformer_%28deep_learning%29#cite_ref-93) Ramesh, Aditya; Pavlov, Mikhail; Goh, Gabriel; Gray, Scott; Voss, Chelsea; Radford, Alec; Chen, Mark; Sutskever, Ilya (2021-02-26). "Zero-Shot Text-to-Image Generation". [arXiv](https://en.wikipedia.org/wiki/ArXiv_%28identifier%29):[2102.12092](https://arxiv.org/abs/2102.12092) \[[cs.CV](https://arxiv.org/archive/cs.CV)\].
92. [↑](https://en.wikipedia.org/wiki/Transformer_%28deep_learning%29#cite_ref-94) Yu, Jiahui; Xu, Yuanzhong; Koh, Jing Yu; Luong, Thang; Baid, Gunjan; Wang, Zirui; Vasudevan, Vijay; Ku, Alexander; Yang, Yinfei (2022-06-21). "Scaling Autoregressive Models for Content-Rich Text-to-Image Generation". [arXiv](https://en.wikipedia.org/wiki/ArXiv_%28identifier%29):[2206.10789](https://arxiv.org/abs/2206.10789) \[[cs.CV](https://arxiv.org/archive/cs.CV)\].
93. [↑](https://en.wikipedia.org/wiki/Transformer_%28deep_learning%29#cite_ref-95) Kariampuzha, William; Alyea, Gioconda; Qu, Sue; Sanjak, Jaleal; Mathé, Ewy; Sid, Eric; Chatelaine, Haley; Yadaw, Arjun; Xu, Yanji; Zhu, Qian (2023). ["Precision information extraction for rare disease epidemiology at scale"](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC9972634). _Journal of Translational Medicine_. **21** (1): 157. [doi](https://en.wikipedia.org/wiki/Doi_%28identifier%29):[10.1186/s12967-023-04011-y](https://doi.org/10.1186%2Fs12967-023-04011-y). [PMC](https://en.wikipedia.org/wiki/PMC_%28identifier%29) [9972634](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC9972634). [PMID](https://en.wikipedia.org/wiki/PMID_%28identifier%29) [36855134](https://pubmed.ncbi.nlm.nih.gov/36855134).
94. [↑](https://en.wikipedia.org/wiki/Transformer_%28deep_learning%29#cite_ref-96) Hsu, Cyril Shih-Huan; Dalgkitsis, Anestis; Grosso, Paola; Papagianni, Chrysa (2026). "Transformer-Empowered Actor-Critic Reinforcement Learning for Sequence-Aware Service Function Chain Partitioning". _IEEE Transactions on Network Science and Engineering_. **13**: 9247–9264. [arXiv](https://en.wikipedia.org/wiki/ArXiv_%28identifier%29):[2504.18902](https://arxiv.org/abs/2504.18902). [Bibcode](https://en.wikipedia.org/wiki/Bibcode_%28identifier%29):[2026ITNSE..13.9247H](https://scixplorer.org/abs/2026ITNSE..13.9247H). [doi](https://en.wikipedia.org/wiki/Doi_%28identifier%29):[10.1109/TNSE.2026.3689920](https://doi.org/10.1109%2FTNSE.2026.3689920).

## Further reading

- Alexander Rush, The Annotated transformer Archived 2021-09-22 at the Wayback Machine, Harvard NLP group, 3 April 2018
- [US patent 10452978](https://worldwide.espacenet.com/textdoc?DB=EPODOC&IDX=US10452978), Noam M. Shazeer; Aidan Nicholas Gomez; Lukasz Mieczyslaw Kaiser; Jakob D. Uszkoreit; Llion Owen Jones; Niki J. Parmar; Illia Polosukhin; Ashish Teku Vaswani, "Attention-based sequence transduction neural networks", issued 2019-10-22,  assigned to Google LLC
- Phuong, Mary; Hutter, Marcus (2022). "Formal Algorithms for Transformers". [arXiv](https://en.wikipedia.org/wiki/ArXiv_%28identifier%29):[2207.09238](https://arxiv.org/abs/2207.09238) \[[cs.LG](https://arxiv.org/archive/cs.LG)\].

|  |  |
| --- | --- |
|  |  |
| Computer programs | AlphaGoVersions [AlphaGo](https://en.wikipedia.org/wiki/AlphaGo) (2015) [Master](https://en.wikipedia.org/wiki/Master_%28software%29) (2016) [AlphaGo Zero](https://en.wikipedia.org/wiki/AlphaGo_Zero) (2017) [AlphaZero](https://en.wikipedia.org/wiki/AlphaZero) (2017) [MuZero](https://en.wikipedia.org/wiki/MuZero) (2019) CompetitionsIn popular culture _[AlphaGo](https://en.wikipedia.org/wiki/AlphaGo_%28film%29)_ (2017) Other [AlphaFold](https://en.wikipedia.org/wiki/AlphaFold) (2018) [AlphaStar](https://en.wikipedia.org/wiki/AlphaStar_%28software%29) (2019) [AlphaTensor](https://en.wikipedia.org/wiki/AlphaTensor) (2022) [AlphaDev](https://en.wikipedia.org/wiki/AlphaDev) (2023) [FunSearch](https://en.wikipedia.org/wiki/FunSearch?action=edit&redlink=1) (2023) [AlphaGeometry](https://en.wikipedia.org/wiki/AlphaGeometry) (2024) [AlphaProof](https://en.wikipedia.org/wiki/Google_DeepMind#AlphaProof) (2024) [AlphaEvolve](https://en.wikipedia.org/wiki/AlphaEvolve) (2025) [AlphaGenome](https://en.wikipedia.org/wiki/AlphaGenome) (2025) |
| Machine learning | Neural networks [Inception](https://en.wikipedia.org/wiki/Inception_%28deep_learning_architecture%29) (2014) [WaveNet](https://en.wikipedia.org/wiki/WaveNet) (2016) [MobileNet](https://en.wikipedia.org/wiki/MobileNet) (2017) [Transformer](https://en.wikipedia.org/wiki/Transformer_%28deep_learning%29) (2017) [EfficientNet](https://en.wikipedia.org/wiki/EfficientNet) (2019) [Gato](https://en.wikipedia.org/wiki/Gato_%28DeepMind%29) (2022) Other |
| Generative AI | Chatbots [Assistant](https://en.wikipedia.org/wiki/Google_Assistant) (2016) [Sparrow](https://en.wikipedia.org/wiki/Sparrow_%28chatbot%29) (2022) [Gemini](https://en.wikipedia.org/wiki/Google_Gemini) (2023) [Nano Banana](https://en.wikipedia.org/wiki/Nano_Banana) (2025) ModelsOther [DreamBooth](https://en.wikipedia.org/wiki/DreamBooth) (2022) [NotebookLM](https://en.wikipedia.org/wiki/NotebookLM) (2023) [Vids](https://en.wikipedia.org/wiki/Google_Vids) (2024) [Gemini Robotics](https://en.wikipedia.org/wiki/Gemini_Robotics) (2025) [Antigravity](https://en.wikipedia.org/wiki/Google_Antigravity) (2025) |
| See also |  |
|  |  |

|  |  |
| --- | --- |
| [History](https://en.wikipedia.org/wiki/History_of_artificial_intelligence) [Glossary](https://en.wikipedia.org/wiki/Glossary_of_artificial_intelligence) Lists |  |
| Concepts |  |
| [Applications](https://en.wikipedia.org/wiki/Applications_of_artificial_intelligence) |  |
| Implementations | Audio–visualTextDecisional[Reasoning systems](https://en.wikipedia.org/wiki/Reasoning_system)[Cognitive architectures](https://en.wikipedia.org/wiki/Cognitive_architecture)[Knowledge bases](https://en.wikipedia.org/wiki/Knowledge_base) |
| People |  |
| Neural network architectures |  |
| Political |  |
| Social and economic |  |
|  |  |

| [Large language models](https://en.wikipedia.org/wiki/Large_language_model) (LLMs) |  |
| --- | --- |
|  |  |
| Concepts |  |
| Training, prompting, and alignment |  |
| Models |  |
| Chatbots and assistants |  |
| Agents, coding, and applications |  |
| Software |  |
| Hardware and infrastructure |  |
| Benchmarks, evaluation, and detection |  |
| Datasets and data |  |
| Organizations |  |
| People |  |
| Social, economic, and governance |  |
|  |  |
