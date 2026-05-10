# Transcript: https://www.youtube.com/watch?v=x9YCcVtnH1M

**Language:** English (auto-generated) (en) — auto-generated
**Snippets:** 245

---

**[00:09]** Hello everyone, my name is Adulia. I am  
**[00:11]** a grad student here at UMass Amherst and  
**[00:14]** this is my project agentic graph rag. So  
**[00:18]** multihop question answering has been a  
**[00:21]** very well-known problem in this field.  
**[00:23]** Most AI retrieval systems are built for  
**[00:25]** simple one question um answering. For  
**[00:29]** example, when was Apple founded? So, you  
**[00:31]** just retrieve the document which has  
**[00:33]** this answer and you're done. But in real  
**[00:35]** world, questions are rarely that simple.  
**[00:38]** Uh for example, uh at the arena where  
**[00:40]** Lewon played, how many people does it  
**[00:42]** seat? So, step one for this would be  
**[00:45]** finding which arena Lewon played in. And  
**[00:47]** then step two would be finding uh its  
**[00:49]** seating capacity. So, two documents, two  
**[00:52]** hops, but one question. This is called a  
**[00:54]** multihop question. uh and then uh to  
**[00:58]** answer this multihop question, the  
**[01:00]** standard retrieval fails because um the  
**[01:04]** standard retrieval sees one chunk at a  
**[01:06]** time and doesn't have the context of the  
**[01:08]** whole doc uh corpus itself.  
**[01:11]** So that's where um knowledge graphs come  
**[01:14]** into play. Uh and we'll look into how  
**[01:17]** the system um solves that um question.  
**[01:21]** So let's look into what a traditional  
**[01:23]** rag is. A traditional rag splits  
**[01:25]** documents into sentences, converts it  
**[01:28]** into vectors, stores the vectors and  
**[01:30]** then finds semantically similar um  
**[01:33]** vectors to your query. So it can answer  
**[01:36]** to your particular question. Um so you  
**[01:39]** just have to find the right document uh  
**[01:42]** and then you have your answer. It's  
**[01:44]** great at finding facts. It's fast but  
**[01:47]** then it's conceptually blind.  
**[01:50]** So that's where graph rag comes into  
**[01:52]** place. Um how a graph rag works is  
**[01:55]** basically it has entities and relations  
**[01:58]** and the uh graph is stored um in like a  
**[02:03]** knowledge graph uh db like for example  
**[02:05]** neoforj  
**[02:07]** um so the way it will be stored is for  
**[02:10]** example let's say u apple which is a  
**[02:13]** company is an entity and we have Steve  
**[02:15]** Jobs who is a founder and then the  
**[02:17]** relationship uh will be very clear and  
**[02:21]** very visual in this graph. So the  
**[02:23]** strength is that it treats the knowledge  
**[02:25]** as a connected network and it's great  
**[02:27]** for multihop reasoning. The limitation  
**[02:30]** is that it can easily go wrong and it's  
**[02:34]** quite fragile because if any entity in  
**[02:37]** this um whole multihop is missing then  
**[02:41]** the connection fails and it just goes  
**[02:43]** goes cold from there. So it is context  
**[02:46]** aware it can answer um for the whole  
**[02:50]** entire corpus but then it has its cons  
**[02:53]** but um but it's still a good sign right  
**[02:56]** but but then still why isn't everyone  
**[02:58]** using it so the number one issue is that  
**[03:01]** it's quite expensive to build in a  
**[03:03]** vector DB you just dump text dump the uh  
**[03:06]** embeddings and save it and it's cheap  
**[03:08]** and fast but then in a graph you must  
**[03:12]** extract the correct entities the correct  
**[03:14]** relationship ships. And so because of  
**[03:16]** that the ingestion is very slow and it's  
**[03:19]** very labor intensive and often it  
**[03:22]** requires um uh people who have a lot of  
**[03:26]** uh domain expertise um to identify and  
**[03:30]** make the graph and um that is very time  
**[03:32]** inensive as well. So our system uh  
**[03:36]** addresses this by building a knowledge  
**[03:38]** graph agentically um uh by inferring the  
**[03:41]** schema directly from the documents. And  
**[03:44]** when it comes to latency, vector search  
**[03:46]** is very fast. It's in milliseconds. But  
**[03:49]** then graph can take time because it has  
**[03:51]** to again traverse uh across multiple  
**[03:54]** paths.  
**[03:56]** So um a graph rag is really it can come  
**[04:00]** in handy especially in fields where you  
**[04:02]** need the exact information. you need  
**[04:04]** very accurate information for example  
**[04:06]** healthcare, finance, legal and it's good  
**[04:09]** with global summarization and it can  
**[04:12]** answer uh multihop questions but at the  
**[04:16]** same time um it needs to be very  
**[04:19]** properly constructed because if you miss  
**[04:22]** any one uh entity it the retrieval  
**[04:26]** fails. So since just building the  
**[04:30]** knowledge graph itself is very labor  
**[04:32]** intensive I was wondering if we can  
**[04:33]** automate it somehow. So that's when I  
**[04:36]** came up with the system uh the agentic  
**[04:38]** graph rack um and with this with the  
**[04:41]** help of multiple agents I am able to  
**[04:44]** build a knowledge graph which is of a  
**[04:46]** decent quality. You can't still compare  
**[04:48]** it to the ideal graph which is handbuilt  
**[04:51]** by people but it's still decent and it  
**[04:54]** provides good results. And um once uh  
**[04:58]** you've constructed an knowledge graph uh  
**[05:01]** via agents uh then later maybe a  
**[05:03]** specialized person can come in and fix  
**[05:05]** the things. But for this experiment  
**[05:07]** purpose I haven't done that. I've built  
**[05:10]** it only using agents and uh to  
**[05:12]** experiment and see the results. So in  
**[05:15]** this particular pipeline I have seven  
**[05:18]** different agents. First agent uh is a  
**[05:21]** schema inference agent which uh infers  
**[05:24]** the schema from the documents and  
**[05:26]** identifies the entities and relationship  
**[05:28]** types. Then comes the entity extraction  
**[05:30]** agent and the relation extraction agent  
**[05:33]** and the schema alignment agent. Uh  
**[05:35]** initially I had a setup where I didn't  
**[05:38]** have so many different agents. I just  
**[05:39]** had uh two or three just the entity  
**[05:42]** extraction and the relation extraction  
**[05:44]** agent and the schema agent. But the  
**[05:47]** quality of the uh knowledge graph that  
**[05:49]** was built was not very great and the  
**[05:52]** performance wasn't that uh good. That's  
**[05:54]** when I introduced a sevenst step uh  
**[05:56]** system and the performance have  
**[05:58]** significantly improved. Um we also have  
**[06:01]** a conflict resolution agent. Um for  
**[06:04]** example, let's say there's a fact that a  
**[06:06]** particular company was founded in a year  
**[06:09]** and there's another fact saying  
**[06:10]** contradicting that uh the year in which  
**[06:13]** it was built. So the conflict resolution  
**[06:16]** agent debates between these two facts  
**[06:18]** and comes to a conclusion on which one's  
**[06:20]** the right thing and then saves that  
**[06:21]** information. We also have a confidence  
**[06:24]** evaluation agent. Um so only um things  
**[06:28]** with a higher confidence uh uh for get  
**[06:33]** stored. So this way a knowledge graph  
**[06:36]** was constructed autonomously using  
**[06:39]** agents. Parallelly I've also used  
**[06:42]** sentence transformer and um created a  
**[06:45]** vector DB and uh stored all the um  
**[06:49]** document text as embeddings in it to  
**[06:52]** compare the results.  
**[06:55]** So this is what the knowledge graph uh  
**[06:58]** looks like  
**[07:00]** and we can query this by using a simple  
**[07:03]** cipher query. Cipher query is very  
**[07:05]** similar to SQL and it's easy to learn  
**[07:07]** and um it's very like you can interpret  
**[07:10]** it uh just by looking at it. So if you  
**[07:13]** look closely u doctor strange is one  
**[07:16]** entity and it is connected to different  
**[07:18]** things like the year Walt Disney Marvel  
**[07:21]** Studios Marvel comics etc.  
**[07:24]** So um so now we have our system we have  
**[07:28]** our vector DB uh things stored in our  
**[07:32]** vector DB and our graph which is  
**[07:34]** autonomously built. So I wanted to test  
**[07:37]** different retrieval meth u methods to  
**[07:40]** find out which is a best retrieval. So  
**[07:43]** we have a vector retrieval, a graph  
**[07:45]** retrieval which is graph traversal and  
**[07:47]** the vector retrieval uses a dense  
**[07:49]** retriever and um a hybrid which is a  
**[07:53]** fusion of both of these  
**[07:59]** and then I've also have uh an  
**[08:01]** orchestrator. Right now the orchestrator  
**[08:04]** just routes queries based on very  
**[08:07]** specific simple rules. Um but in the  
**[08:10]** future we can after we have a lot of  
**[08:12]** data we can train it to route particular  
**[08:15]** queries to those um retrieval which will  
**[08:19]** give us the best results after learning  
**[08:21]** from the results.  
**[08:24]** And I also have a few agents to track  
**[08:26]** the performance. And this was the  
**[08:29]** initial test setup. Uh took a small  
**[08:32]** corpus of 25 documents uh and 25 queries  
**[08:35]** and its related documents. And the these  
**[08:39]** are the basic stats for the um nodes and  
**[08:43]** relationships of the graph. And then the  
**[08:46]** vector embedding size.  
**[08:49]** And the results are in. uh hybrid has  
**[08:53]** outperformed both the vector and graph.  
**[08:56]** So these results are interesting uh  
**[08:59]** because um I expected graph to do better  
**[09:03]** but graph actually fails more often than  
**[09:07]** we think because the entities are not  
**[09:10]** perfect like I mentioned earlier if the  
**[09:13]** very first entity is missing like it  
**[09:16]** can't really hop on anything so it just  
**[09:18]** goes cold or sometimes when we are  
**[09:20]** hopping multiple times if there's one  
**[09:23]** entity in the middle that's missing it  
**[09:25]** goes cold again  
**[09:27]** um and uh vector is just a straight  
**[09:31]** dense retrieval um semantic similarity  
**[09:34]** based um retrieval and the uh hybrid is  
**[09:38]** actually the best of both worlds. So how  
**[09:41]** hybrid works is that vector runs first  
**[09:45]** um the fa uh it searches for  
**[09:48]** semantically similar sentences and gets  
**[09:51]** the correct entity and once the entity  
**[09:54]** uh is at hand the graph expands upon it  
**[09:58]** and once we have that uh we combine it  
**[10:02]** dduplicate it um so basically graph and  
**[10:06]** vector both has its uh strengths and  
**[10:10]** hybrid is a good combination and it it  
**[10:13]** covers both. It miss it catches things  
**[10:16]** with which hybrid um sorry vector misses  
**[10:19]** and it catches things which graph also  
**[10:22]** misses.  
**[10:24]** So um that is a conclusion. The hybrid  
**[10:28]** um is actually doing pretty well uh with  
**[10:31]** an exact match score of 68%.  
**[10:34]** uh outperforming both the vector and the  
**[10:37]** graph only retrieval. And the other key  
**[10:41]** finding is that the agentic graph uh rag  
**[10:44]** which was built the results are very  
**[10:47]** similar to um the ideal m ideal  
**[10:51]** knowledge graph which is built. Um so I  
**[10:54]** think the results are like pretty  
**[10:56]** comparable and the ceiling for this  
**[11:00]** another thing which I have noted was  
**[11:02]** that the ceiling is um we have an LLM  
**[11:04]** answering layer that particularly  
**[11:07]** sometimes even if you have you give it  
**[11:10]** the right answer um right document you  
**[11:14]** fetch the right document with the  
**[11:15]** retrieval and give it to it still  
**[11:18]** sometimes gives us the wrong answer it's  
**[11:21]** because of various reasons like ll MS  
**[11:23]** hallucinating and things like that. So  
**[11:25]** that's a ceiling. But um but overall  
**[11:28]** this we found that hybrid retrieval is a  
**[11:32]** very good method to go ahead with and uh  
**[11:35]** it outperforms both. And that concludes  
**[11:38]** my presentation.  