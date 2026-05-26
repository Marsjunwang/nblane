# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: tests/e2e/_walkthrough.spec.ts >> walkthrough
- Location: tests/e2e/_walkthrough.spec.ts:30:1

# Error details

```
Error: expect(received).toHaveLength(expected)

Expected length: 0
Received length: 1
Received array:  ["console.error: Failed to load resource: net::ERR_CONNECTION_RESET"]
```

# Page snapshot

```yaml
- generic [ref=e3]:
  - generic [ref=e4]:
    - generic "Attention Is All You Need" [ref=e5]
    - generic [ref=e6]:
      - button "<" [ref=e7] [cursor=pointer]
      - generic [ref=e8]: Page 1 / 15
      - generic "Structured text ready" [ref=e9]
      - textbox [ref=e10]: "1"
      - generic [ref=e11]: / 15
      - button ">" [ref=e12] [cursor=pointer]
      - button "-" [ref=e13] [cursor=pointer]
      - button "+" [ref=e14] [cursor=pointer]
      - button "Fit width" [ref=e15] [cursor=pointer]
      - button "Fit page" [ref=e16] [cursor=pointer]
      - button "1:1" [ref=e17] [cursor=pointer]
    - generic [ref=e18]:
      - button "PDF" [ref=e19] [cursor=pointer]
      - button "Compare" [ref=e20] [cursor=pointer]
      - button "Translation only" [ref=e21] [cursor=pointer]
      - button "⇅" [pressed] [ref=e22] [cursor=pointer]
    - generic [ref=e23]:
      - button "Full translation" [ref=e24] [cursor=pointer]
      - button "Analyze Paper" [ref=e25] [cursor=pointer]
      - button "Deep read" [ref=e26] [cursor=pointer]
      - button "Save progress" [ref=e27] [cursor=pointer]
      - button "Fullscreen" [ref=e28] [cursor=pointer]
      - button "Panel" [active] [ref=e29] [cursor=pointer]
      - generic [ref=e30]: "Reader writes stay candidate-first: translate, annotate, cite, then review before promotion."
  - main [ref=e31]:
    - complementary [ref=e32]:
      - generic [ref=e33]:
        - button "Outline" [ref=e34] [cursor=pointer]
        - button "Pages" [ref=e35] [cursor=pointer]
        - button "Search" [ref=e36] [cursor=pointer]
        - button "<" [ref=e37] [cursor=pointer]
      - generic [ref=e39]:
        - button "Abstract Page 1" [ref=e40] [cursor=pointer]:
          - generic [ref=e41]: Abstract
          - generic [ref=e42]: Page 1
        - button "Introduction Page 2" [ref=e43] [cursor=pointer]:
          - generic [ref=e44]: Introduction
          - generic [ref=e45]: Page 2
        - button "Background Page 2" [ref=e46] [cursor=pointer]:
          - generic [ref=e47]: Background
          - generic [ref=e48]: Page 2
        - button "6.3 English Constituency Parsing English Constituency Parsing Page 9" [ref=e49] [cursor=pointer]:
          - generic [ref=e50]: 6.3 English Constituency Parsing English Constituency Parsing
          - generic [ref=e51]: Page 9
    - generic [ref=e53]:
      - article [ref=e54]:
        - generic [ref=e55]: Page 1
        - generic [ref=e58]: Provided proper attribution is provided, Google hereby grants permission to reproduce the tables and figures in this paper solely for use in journalistic or scholarly works. Attention Is All You Need Ashish Vaswani ∗ Google Brain avaswani@google.com Noam Shazeer ∗ Google Brain noam@google.com Niki Parmar ∗ Google Research nikip@google.com Jakob Uszkoreit ∗ Google Research usz@google.com Llion Jones ∗ Google Research llion@google.com Aidan N. Gomez ∗ † University of Toronto aidan@cs.toronto.edu Łukasz Kaiser ∗ Google Brain lukaszkaiser@google.com Illia Polosukhin ∗ ‡ illia.polosukhin@gmail.com Abstract The dominant sequence transduction models are based on complex recurrent or convolutional neural networks that include an encoder and a decoder. The best performing models also connect the encoder and decoder through an attention mechanism. We propose a new simple network architecture, the Transformer, based solely on attention mechanisms, dispensing with recurrence and convolutions entirely. Experiments on two machine translation tasks show these models to be superior in quality while being more parallelizable and requiring significantly less time to train. Our model achieves 28.4 BLEU on the WMT 2014 English- to-German translation task, improving over the existing best results, including ensembles, by over 2 BLEU. On the WMT 2014 English-to-French translation task, our model establishes a new single-model state-of-the-art BLEU score of 41.8 after training for 3.5 days on eight GPUs, a small fraction of the training costs of the best models from the literature. We show that the Transformer generalizes well to other tasks by applying it successfully to English constituency parsing both with large and limited training data. ∗ Equal contribution. Listing order is random. Jakob proposed replacing RNNs with self-attention and started the effort to evaluate this idea. Ashish, with Illia, designed and implemented the first Transformer models and has been crucially involved in every aspect of this work. Noam proposed scaled dot-product attention, multi-head attention and the parameter-free position representation and became the other person involved in nearly every detail. Niki designed, implemented, tuned and evaluated countless model variants in our original codebase and tensor2tensor. Llion also experimented with novel model variants, was responsible for our initial codebase, and efficient inference and visualizations. Lukasz and Aidan spent countless long days designing various parts of and implementing tensor2tensor, replacing our earlier codebase, greatly improving results and massively accelerating our research. † Work performed while at Google Brain. ‡ Work performed while at Google Research. 31st Conference on Neural Information Processing Systems (NIPS 2017), Long Beach, CA, USA. arXiv:1706.03762v7 [cs.CL] 2 Aug 2023
      - article [ref=e59]:
        - generic [ref=e60]: Page 2
        - generic [ref=e63]: 1 Introduction Recurrent neural networks, long short-term memory [ 13 ] and gated recurrent [ 7 ] neural networks in particular, have been firmly established as state of the art approaches in sequence modeling and transduction problems such as language modeling and machine translation [ 35 , 2 , 5 ]. Numerous efforts have since continued to push the boundaries of recurrent language models and encoder-decoder architectures [38, 24, 15]. Recurrent models typically factor computation along the symbol positions of the input and output sequences. Aligning the positions to steps in computation time, they generate a sequence of hidden states h t , as a function of the previous hidden state h t − 1 and the input for position t . This inherently sequential nature precludes parallelization within training examples, which becomes critical at longer sequence lengths, as memory constraints limit batching across examples. Recent work has achieved significant improvements in computational efficiency through factorization tricks [ 21 ] and conditional computation [ 32 ], while also improving model performance in case of the latter. The fundamental constraint of sequential computation, however, remains. Attention mechanisms have become an integral part of compelling sequence modeling and transduc- tion models in various tasks, allowing modeling of dependencies without regard to their distance in the input or output sequences [ 2 , 19 ]. In all but a few cases [ 27 ], however, such attention mechanisms are used in conjunction with a recurrent network. In this work we propose the Transformer, a model architecture eschewing recurrence and instead relying entirely on an attention mechanism to draw global dependencies between input and output. The Transformer allows for significantly more parallelization and can reach a new state of the art in translation quality after being trained for as little as twelve hours on eight P100 GPUs. 2 Background The goal of reducing sequential computation also forms the foundation of the Extended Neural GPU [ 16 ], ByteNet [ 18 ] and ConvS2S [ 9 ], all of which use convolutional neural networks as basic building block, computing hidden representations in parallel for all input and output positions. In these models, the number of operations required to relate signals from two arbitrary input or output positions grows in the distance between positions, linearly for ConvS2S and logarithmically for ByteNet. This makes it more difficult to learn dependencies between distant positions [ 12 ]. In the Transformer this is reduced to a constant number of operations, albeit at the cost of reduced effective resolution due to averaging attention-weighted positions, an effect we counteract with Multi-Head Attention as described in section 3.2. Self-attention, sometimes called intra-attention is an attention mechanism relating different positions of a single sequence in order to compute a representation of the sequence. Self-attention has been used successfully in a variety of tasks including reading comprehension, abstractive summarization, textual entailment and learning task-independent sentence representations [4, 27, 28, 22]. End-to-end memory networks are based on a recurrent attention mechanism instead of sequence- aligned recurrence and have been shown to perform well on simple-language question answering and language modeling tasks [34]. To the best of our knowledge, however, the Transformer is the first transduction model relying entirely on self-attention to compute representations of its input and output without using sequence- aligned RNNs or convolution. In the following sections, we will describe the Transformer, motivate self-attention and discuss its advantages over models such as [17, 18] and [9]. 3 Model Architecture Most competitive neural sequence transduction models have an encoder-decoder structure [ 5 , 2 , 35 ]. Here, the encoder maps an input sequence of symbol representations ( x 1 , ..., x n ) to a sequence of continuous representations z = ( z 1 , ..., z n ) . Given z , the decoder then generates an output sequence ( y 1 , ..., y m ) of symbols one element at a time. At each step the model is auto-regressive [10], consuming the previously generated symbols as additional input when generating the next. 2
      - article [ref=e64]:
        - generic [ref=e65]: Page 3
        - generic [ref=e68]: "Figure 1: The Transformer - model architecture. The Transformer follows this overall architecture using stacked self-attention and point-wise, fully connected layers for both the encoder and decoder, shown in the left and right halves of Figure 1, respectively. 3.1 Encoder and Decoder Stacks Encoder: The encoder is composed of a stack of N = 6 identical layers. Each layer has two sub-layers. The first is a multi-head self-attention mechanism, and the second is a simple, position- wise fully connected feed-forward network. We employ a residual connection [ 11 ] around each of the two sub-layers, followed by layer normalization [ 1 ]. That is, the output of each sub-layer is LayerNorm( x + Sublayer( x )) , where Sublayer( x ) is the function implemented by the sub-layer itself. To facilitate these residual connections, all sub-layers in the model, as well as the embedding layers, produce outputs of dimension d model = 512 . Decoder: The decoder is also composed of a stack of N = 6 identical layers. In addition to the two sub-layers in each encoder layer, the decoder inserts a third sub-layer, which performs multi-head attention over the output of the encoder stack. Similar to the encoder, we employ residual connections around each of the sub-layers, followed by layer normalization. We also modify the self-attention sub-layer in the decoder stack to prevent positions from attending to subsequent positions. This masking, combined with fact that the output embeddings are offset by one position, ensures that the predictions for position i can depend only on the known outputs at positions less than i . 3.2 Attention An attention function can be described as mapping a query and a set of key-value pairs to an output, where the query, keys, values, and output are all vectors. The output is computed as a weighted sum 3"
      - article [ref=e69]:
        - generic [ref=e70]: Page 4
        - generic [ref=e73]: "Scaled Dot-Product Attention Multi-Head Attention Figure 2: (left) Scaled Dot-Product Attention. (right) Multi-Head Attention consists of several attention layers running in parallel. of the values, where the weight assigned to each value is computed by a compatibility function of the query with the corresponding key. 3.2.1 Scaled Dot-Product Attention We call our particular attention \"Scaled Dot-Product Attention\" (Figure 2). The input consists of queries and keys of dimension d k , and values of dimension d v . We compute the dot products of the query with all keys, divide each by √ d k , and apply a softmax function to obtain the weights on the values. In practice, we compute the attention function on a set of queries simultaneously, packed together into a matrix Q . The keys and values are also packed together into matrices K and V . We compute the matrix of outputs as: Attention( Q, K, V ) = softmax( QK T √ d k ) V (1) The two most commonly used attention functions are additive attention [ 2 ], and dot-product (multi- plicative) attention. Dot-product attention is identical to our algorithm, except for the scaling factor of 1 √ d k . Additive attention computes the compatibility function using a feed-forward network with a single hidden layer. While the two are similar in theoretical complexity, dot-product attention is much faster and more space-efficient in practice, since it can be implemented using highly optimized matrix multiplication code. While for small values of d k the two mechanisms perform similarly, additive attention outperforms dot product attention without scaling for larger values of d k [ 3 ]. We suspect that for large values of d k , the dot products grow large in magnitude, pushing the softmax function into regions where it has extremely small gradients 4 . To counteract this effect, we scale the dot products by 1 √ d k . 3.2.2 Multi-Head Attention Instead of performing a single attention function with d model -dimensional keys, values and queries, we found it beneficial to linearly project the queries, keys and values h times with different, learned linear projections to d k , d k and d v dimensions, respectively. On each of these projected versions of queries, keys and values we then perform the attention function in parallel, yielding d v -dimensional 4 To illustrate why the dot products get large, assume that the components of q and k are independent random variables with mean 0 and variance 1 . Then their dot product, q · k = P d k i =1 q i k i , has mean 0 and variance d k . 4"
      - article [ref=e74]:
        - generic [ref=e75]: Page 5
        - generic [ref=e78]: "output values. These are concatenated and once again projected, resulting in the final values, as depicted in Figure 2. Multi-head attention allows the model to jointly attend to information from different representation subspaces at different positions. With a single attention head, averaging inhibits this. MultiHead( Q, K, V ) = Concat(head 1 , ..., head h ) W O where head i = Attention( QW Q i , KW K i , V W V i ) Where the projections are parameter matrices W Q i ∈ R d model × d k , W K i ∈ R d model × d k , W V i ∈ R d model × d v and W O ∈ R hd v × d model . In this work we employ h = 8 parallel attention layers, or heads. For each of these we use d k = d v = d model /h = 64 . Due to the reduced dimension of each head, the total computational cost is similar to that of single-head attention with full dimensionality. 3.2.3 Applications of Attention in our Model The Transformer uses multi-head attention in three different ways: • In \"encoder-decoder attention\" layers, the queries come from the previous decoder layer, and the memory keys and values come from the output of the encoder. This allows every position in the decoder to attend over all positions in the input sequence. This mimics the typical encoder-decoder attention mechanisms in sequence-to-sequence models such as [38, 2, 9]. • The encoder contains self-attention layers. In a self-attention layer all of the keys, values and queries come from the same place, in this case, the output of the previous layer in the encoder. Each position in the encoder can attend to all positions in the previous layer of the encoder. • Similarly, self-attention layers in the decoder allow each position in the decoder to attend to all positions in the decoder up to and including that position. We need to prevent leftward information flow in the decoder to preserve the auto-regressive property. We implement this inside of scaled dot-product attention by masking out (setting to −∞ ) all values in the input of the softmax which correspond to illegal connections. See Figure 2. 3.3 Position-wise Feed-Forward Networks In addition to attention sub-layers, each of the layers in our encoder and decoder contains a fully connected feed-forward network, which is applied to each position separately and identically. This consists of two linear transformations with a ReLU activation in between. FFN( x ) = max(0 , xW 1 + b 1 ) W 2 + b 2 (2) While the linear transformations are the same across different positions, they use different parameters from layer to layer. Another way of describing this is as two convolutions with kernel size 1. The dimensionality of input and output is d model = 512 , and the inner-layer has dimensionality d f f = 2048 . 3.4 Embeddings and Softmax Similarly to other sequence transduction models, we use learned embeddings to convert the input tokens and output tokens to vectors of dimension d model . We also use the usual learned linear transfor- mation and softmax function to convert the decoder output to predicted next-token probabilities. In our model, we share the same weight matrix between the two embedding layers and the pre-softmax linear transformation, similar to [ 30 ]. In the embedding layers, we multiply those weights by √ d model . 5"
      - article [ref=e79]:
        - generic [ref=e80]: Page 6
        - generic [ref=e82]: Loading PDF...
      - article [ref=e85]:
        - generic [ref=e86]: Page 7
        - generic [ref=e88]: Loading PDF...
      - article [ref=e91]:
        - generic [ref=e92]: Page 8
        - generic [ref=e94]: Loading PDF...
      - article [ref=e97]:
        - generic [ref=e98]: Page 9
        - generic [ref=e100]: Loading PDF...
      - article [ref=e103]:
        - generic [ref=e104]: Page 10
        - generic [ref=e106]: Loading PDF...
      - article [ref=e109]:
        - generic [ref=e110]: Page 11
        - generic [ref=e112]: Loading PDF...
      - article [ref=e115]:
        - generic [ref=e116]: Page 12
        - generic [ref=e118]: Loading PDF...
      - article [ref=e121]:
        - generic [ref=e122]: Page 13
        - generic [ref=e124]: Loading PDF...
      - article [ref=e127]:
        - generic [ref=e128]: Page 14
        - generic [ref=e130]: Loading PDF...
      - article [ref=e133]:
        - generic [ref=e134]: Page 15
        - generic [ref=e136]: Loading PDF...
    - complementary [ref=e139]:
      - generic "Panel" [ref=e140]
      - generic [ref=e141]:
        - generic [ref=e142]:
          - button "Notes" [ref=e143] [cursor=pointer]
          - button "Translation" [ref=e144] [cursor=pointer]
          - button "Review" [ref=e145] [cursor=pointer]
          - button "Claims" [ref=e146] [cursor=pointer]
        - generic [ref=e147]:
          - generic [ref=e148]:
            - button "Current page" [ref=e149] [cursor=pointer]
            - button "All" [ref=e150] [cursor=pointer]
          - generic [ref=e151]: No items yet
      - generic [ref=e152]:
        - generic [ref=e153]: Ask
        - generic [ref=e154]:
          - textbox "Question" [ref=e155]
          - button "Ask" [ref=e156] [cursor=pointer]
```

# Test source

```ts
  19  |       activeLeftTab: (document.querySelector(".pr-left-rail-tab.active") as HTMLElement)?.textContent || "?",
  20  |       visibleErrorBoxes: document.querySelectorAll(".pr-error").length,
  21  |       progressBarVisible: document.querySelector("#translationProgressShell")?.classList.contains("visible") || false,
  22  |       bulkLoaded: !!(window as any).bulkTranslations?.segments?.length,
  23  |       payloadEtag: (window as any).payloadEtag || "",
  24  |       sidePanelTabs: Array.from(document.querySelectorAll(".pr-side-tab")).map((t) => (t as HTMLElement).textContent),
  25  |     };
  26  |   });
  27  |   console.log(`[${label}]`, JSON.stringify(data, null, 2));
  28  | }
  29  | 
  30  | test("walkthrough", async ({ page }) => {
  31  |   if (!READER_URL) test.skip();
  32  | 
  33  |   const errors: string[] = [];
  34  |   const networkSummary: { url: string; status: number; type: string }[] = [];
  35  |   page.on("pageerror", (err) => errors.push(`pageerror: ${err.message}`));
  36  |   page.on("console", (msg) => {
  37  |     if (msg.type() === "error") errors.push(`console.error: ${msg.text()}`);
  38  |   });
  39  |   page.on("response", (resp) => {
  40  |     const url = resp.url();
  41  |     if (/\/reader\/api\/.+\/(payload|translations\/bulk|page-preview|page-text-layer|tasks)/.test(url)) {
  42  |       networkSummary.push({ url: url.replace(/[?&]reader_token=[^&]+/, ""), status: resp.status(), type: resp.request().method() });
  43  |     }
  44  |   });
  45  | 
  46  |   // 1) Initial load (PDF mode default)
  47  |   await page.goto(READER_URL, { waitUntil: "domcontentloaded" });
  48  |   await page.waitForFunction(
  49  |     () => (document.getElementById("root")?.innerHTML?.length || 0) > 5000,
  50  |     { timeout: 20000 },
  51  |   );
  52  |   await page.waitForTimeout(3000);  // let bulk + first 1-2 page renders settle
  53  |   await page.screenshot({ path: "/tmp/walkthrough-1-pdf-mode.png", fullPage: false });
  54  |   await dumpDiagnostics(page, "PDF mode after load");
  55  | 
  56  |   // 2) Switch to compare mode
  57  |   const compareBtn = page.locator('.pr-mode [data-mode="compare"]');
  58  |   if (await compareBtn.count() > 0) {
  59  |     await compareBtn.click();
  60  |     await page.waitForTimeout(2500);
  61  |     await page.screenshot({ path: "/tmp/walkthrough-2-compare-mode.png", fullPage: false });
  62  |     await dumpDiagnostics(page, "Compare mode");
  63  |   }
  64  | 
  65  |   // 3) Switch to translation-only mode
  66  |   const transBtn = page.locator('.pr-mode [data-mode="translation"]');
  67  |   if (await transBtn.count() > 0) {
  68  |     await transBtn.click();
  69  |     await page.waitForTimeout(2500);
  70  |     await page.screenshot({ path: "/tmp/walkthrough-3-translation-mode.png", fullPage: false });
  71  |     await dumpDiagnostics(page, "Translation-only mode");
  72  |   }
  73  | 
  74  |   // 4) Scroll the translation view a few pages
  75  |   await page.evaluate(() => {
  76  |     const scrollEl = document.getElementById("translationReader") || document.querySelector(".pr-translation-body");
  77  |     if (scrollEl) (scrollEl as HTMLElement).scrollBy(0, 1500);
  78  |   });
  79  |   await page.waitForTimeout(1500);
  80  |   await page.screenshot({ path: "/tmp/walkthrough-4-translation-scrolled.png", fullPage: false });
  81  | 
  82  |   // 5) Back to PDF mode and try the side panel "review" tab to see analyze/deep_read output
  83  |   const pdfBtn = page.locator('.pr-mode [data-mode="pdf"]');
  84  |   if (await pdfBtn.count() > 0) {
  85  |     await pdfBtn.click();
  86  |     await page.waitForTimeout(1500);
  87  |   }
  88  |   // Open side panel if collapsed
  89  |   const sideBtn = page.locator('[data-action="togglePanel"]').first();
  90  |   if (await sideBtn.count() > 0) {
  91  |     await sideBtn.click();
  92  |     await page.waitForTimeout(500);
  93  |   }
  94  |   // Click the "review" / "Analyze Paper" tab
  95  |   const reviewTab = page.locator('.pr-side-tab').filter({ hasText: /review|analy|分析/i }).first();
  96  |   if (await reviewTab.count() > 0) {
  97  |     await reviewTab.click();
  98  |     await page.waitForTimeout(800);
  99  |     await page.screenshot({ path: "/tmp/walkthrough-5-review-panel.png", fullPage: false });
  100 |     await dumpDiagnostics(page, "Review panel");
  101 |   }
  102 | 
  103 |   console.log("\n=== Network summary (de-tokenized) ===");
  104 |   console.log(`Total relevant requests: ${networkSummary.length}`);
  105 |   const byEndpoint: Record<string, { count: number; statuses: Record<number, number> }> = {};
  106 |   for (const r of networkSummary) {
  107 |     const key = r.url.replace(/\/api\/[^/]+\//, "/api/{src}/").replace(/\/\d+($|\?)/, "/{n}");
  108 |     byEndpoint[key] = byEndpoint[key] || { count: 0, statuses: {} };
  109 |     byEndpoint[key].count++;
  110 |     byEndpoint[key].statuses[r.status] = (byEndpoint[key].statuses[r.status] || 0) + 1;
  111 |   }
  112 |   for (const [endpoint, info] of Object.entries(byEndpoint)) {
  113 |     console.log(`  ${endpoint}: ${info.count} hits, statuses: ${JSON.stringify(info.statuses)}`);
  114 |   }
  115 |   console.log("\n=== JS errors ===");
  116 |   for (const e of errors) console.log(e);
  117 | 
  118 |   // Don't fail on aesthetic issues — this is a walk-through dump
> 119 |   expect(errors.filter(e => !/PDF\.js|pdf\.worker/i.test(e))).toHaveLength(0);
      |                                                               ^ Error: expect(received).toHaveLength(expected)
  120 | });
  121 | 
```