# Transcript: https://www.youtube.com/watch?v=SYU5Bn7B98A

**Language:** English (auto-generated) (en) — auto-generated
**Snippets:** 557

---

**[00:08]** Hello everyone. Thank you for your  
**[00:10]** patience and apologies for the delay.  
**[00:11]** Um, welcome to graph reader agentic  
**[00:13]** rathinking long context retrieval  
**[00:16]** systems. Today presenting will be Jayata  
**[00:18]** Batara and Somia Ranjandas. Somia is  
**[00:22]** going to be joining us shortly but I'll  
**[00:23]** hand it over to Jada to take it away.  
**[00:25]** >> All righty. Uh, are we good to go?  
**[00:29]** Okay. Uh so hey everyone thank you for  
**[00:32]** joining in and we're going to discuss  
**[00:33]** about a very interesting topic today  
**[00:35]** called graph reader uh agentic rag  
**[00:37]** rethinking long context retrieval  
**[00:39]** systems. So uh this is a uh paper  
**[00:42]** research paper implementation with the  
**[00:44]** same name graph reader that uh came out  
**[00:46]** around last year November by uh uh some  
**[00:50]** of the researchers at Alibaba group and  
**[00:52]** other institutes and um so our our our  
**[00:56]** uh take is a bit different from what has  
**[00:58]** been uh discussed in the paper. Uh there  
**[01:01]** they have used closed source models. So  
**[01:04]** we tried to um reproduce the same using  
**[01:06]** open-source models and tools and also we  
**[01:09]** tried to uh implement on top of what has  
**[01:12]** already been done and we'll be  
**[01:14]** discussing uh all of those today. So  
**[01:17]** let's get uh rolling and uh we'll be uh  
**[01:22]** basically trying to cover what uh  
**[01:24]** traditional gra challenges are and how  
**[01:27]** uh graph reader helps you overcome that.  
**[01:30]** And graph reader is basically graph rag  
**[01:33]** plus agents and we'll see how you can  
**[01:35]** construct one and go through the  
**[01:37]** traversal and retrieval process and  
**[01:39]** what's better than showing you a demo a  
**[01:42]** live demo uh that we have uh  
**[01:44]** implemented. So uh on that note let's  
**[01:48]** let's try to address uh what is the what  
**[01:50]** are the problems that you face while  
**[01:52]** building uh search and retrieval  
**[01:54]** systems. uh so uh most of us uh have  
**[01:57]** already I'm sure been working with some  
**[01:59]** kind or the other uh with the rack  
**[02:02]** systems and uh they they uh uh when you  
**[02:05]** implement a knife rag you always you  
**[02:08]** cannot expect to uh get the best of  
**[02:10]** answers from your knowledge base. So  
**[02:13]** essentially uh these are the uh three  
**[02:16]** problems broad problems that we have  
**[02:18]** identified when you go on to implement  
**[02:20]** rack systems. uh first uh is the long uh  
**[02:24]** the context window limitations that most  
**[02:26]** of the LLMs have and it also is the  
**[02:29]** matter that even if with long context  
**[02:31]** windows like 2 million token lens uh  
**[02:33]** there is a problem of lost in the middle  
**[02:35]** or needle in the hashtag problem. So  
**[02:37]** these have uh been overcome by some way  
**[02:40]** or the other like uh KV caching and and  
**[02:43]** pretty uh other uh methods of rag that  
**[02:46]** you can implement like uh uh the  
**[02:48]** adaptive rag or the corrective rag  
**[02:51]** methods and agent take ways have also  
**[02:53]** been implemented to overcome this. Maybe  
**[02:56]** you badge your uh processes. Uh then the  
**[02:59]** next one that that comes into picture is  
**[03:01]** is uh the state and persistent issues.  
**[03:04]** So, LLMs do not have the memory of their  
**[03:07]** own. But when you are building such rack  
**[03:09]** systems, you need to maintain certain  
**[03:11]** kind of uh uh uh temporary memory which  
**[03:15]** will uh help you process through the  
**[03:17]** next steps onto the actions that you  
**[03:19]** need to next take in your pipeline. So  
**[03:22]** these also have been overcome uh in in  
**[03:25]** some ways. Uh there are memory layers  
**[03:27]** that you can append and even these  
**[03:29]** agentic architectures they they have a  
**[03:32]** memory built into it.  
**[03:34]** Uh the third problem is when you  
**[03:36]** implement uh knowledge graphs there is a  
**[03:38]** big big uh gap when you need to build an  
**[03:41]** ontology or the schema. So without  
**[03:43]** propermemes or architects this is a a  
**[03:47]** big problem for developers to  
**[03:52]** build it. Uh so these these are the main  
**[03:54]** challenges that that we identified are  
**[03:56]** are causing a hindrance onto when we  
**[03:58]** implement rag. So uh we we say that  
**[04:02]** enter a graph reader which is a graph  
**[04:04]** based agentic system designed to um  
**[04:07]** supercharge your long context windows uh  
**[04:10]** both in injection as well as retrieval.  
**[04:13]** So uh what graph reader uh the paper pro  
**[04:15]** proposes us to is that instead of uh  
**[04:18]** having to read documents linearly what  
**[04:21]** you can do is uh you can reconstruct a  
**[04:23]** graph of atomic facts and relationships  
**[04:26]** then use a intelligent agent to explore  
**[04:29]** the graph in a goal directed way. So  
**[04:32]** we'll demystify all of all of this that  
**[04:35]** we uh that the definition says and I  
**[04:38]** call graph reader a healer because it  
**[04:41]** has uh overcome challenges in every step  
**[04:43]** of rack that we do starting from uh  
**[04:46]** chunking to uh retrieval to reflection  
**[04:49]** to context window and multihop uh  
**[04:52]** reasoning as well. So so the way that uh  
**[04:55]** graph reader works is that it first  
**[04:57]** constructs your graph. The input  
**[04:59]** document is broken down into chunks and  
**[05:01]** it has the identified key entities,  
**[05:04]** facts, their relationships and extract  
**[05:06]** it in a form of a graph and then you go  
**[05:09]** forward with planning and exploration uh  
**[05:12]** where you can uh when given a question  
**[05:14]** the agent tries to create a plan. It  
**[05:16]** decides where to start, where what to  
**[05:18]** read and how to proceed. It uses a  
**[05:20]** predefined tool to read uh node uh the  
**[05:24]** read the nodes its contents as well as  
**[05:26]** its neighbors and then comes the uh  
**[05:30]** shallow retrieve uh the context codes to  
**[05:32]** find uh fine reasoning as well. It  
**[05:34]** begins with uh summaries or uh and then  
**[05:37]** tries to drill down to the uh end node  
**[05:40]** and then try to optimize your token  
**[05:42]** usage as well. Uh there is a reflection  
**[05:45]** and uh note takingaking. So in in you  
**[05:47]** can think of it uh as a scratch pad that  
**[05:49]** uh the agent maintains on updating uh  
**[05:52]** the action plan it needs to take at  
**[05:54]** every step with the learnings that it is  
**[05:57]** doing and that is an iterative process  
**[05:59]** that it continues and finally of course  
**[06:01]** you have the LLM to synthesize all of  
**[06:04]** these uh knowledge that it gathered to  
**[06:06]** give you the information.  
**[06:10]** So uh this is how how the uh paper had  
**[06:13]** proposed like uh it first takes in the  
**[06:16]** document splits it into chunks. In the  
**[06:19]** paper uh they have maintained a  
**[06:20]** paragraph structure while while  
**[06:22]** chunking. However uh this is a bit hard  
**[06:24]** when you do it in your generic way.  
**[06:26]** Therefore we can use a chunking suitable  
**[06:29]** to your use case. Uh the next step is  
**[06:32]** each chunk is processed uh in the by the  
**[06:34]** LLM to identify atomic facts which are  
**[06:36]** smallest in indivisible units of  
**[06:40]** information that capture core uh  
**[06:42]** details. So say suppose I say a sentence  
**[06:44]** that Ja works for Deoid and is here to  
**[06:48]** give a session with Somia. An atomic  
**[06:50]** fact could be broken down into something  
**[06:52]** like Jita works at Deoid and Jita is  
**[06:55]** giving a session with Somia. uh each  
**[06:58]** atomic fact is focused on one clear  
**[07:00]** standalone piece of information. For  
**[07:02]** these atomic facts and key elements are  
**[07:05]** identified for the first fact the key  
**[07:08]** element could be deoid and joa. For the  
**[07:10]** second it could be joita today session  
**[07:14]** and somia. These key elements are  
**[07:16]** essentially essentially proper nouns  
**[07:19]** that capture the core meaning of the  
**[07:21]** atomic fact that you have in your  
**[07:22]** information. Uh this is a a rough uh  
**[07:26]** prompt that uh was proposed in the paper  
**[07:28]** that you define what your key elements  
**[07:30]** atomic facts are. You say certain kinds  
**[07:32]** of requirements that you have that do  
**[07:34]** not exceed so and so uh token limit and  
**[07:37]** and other essential facts and you also  
**[07:39]** give it some examples so that the LLM is  
**[07:41]** able to reference it better. Uh during  
**[07:45]** the graph exploration uh this is the uh  
**[07:48]** process that uh it formulates. uh I'm  
**[07:51]** not going into going to deep dive into  
**[07:53]** it because uh we have implemented a a  
**[07:55]** different uh we have taken inspiration  
**[07:57]** but uh developed on top of it. So I'll  
**[08:00]** hand over to my co-presenter Somia to  
**[08:03]** discuss further  
**[08:10]** uh Sam are you able to share your screen  
**[08:12]** or do you want me to continue?  
**[08:27]** Okay. Uh  
**[08:29]** let me let me share my VS code.  
**[09:10]** Is is my screen whisper.  
**[09:26]** Okay. Probably I'm not sure why this  
**[09:29]** code is not uh we shut up. We try  
**[09:34]** edition.  
**[09:44]** I hope it is uh visible now.  
**[09:53]** Okay.  
**[09:56]** So uh we tried to implement it using  
**[09:59]** Neo4j and Langraph which is a very  
**[10:03]** popularly known uh agentic u argentic  
**[10:08]** library that you can use of and along  
**[10:10]** with that we we installed all the  
**[10:12]** necessary open-source uh other suitable  
**[10:16]** libraries that we will be needing like  
**[10:17]** sentence transformers for embedding and  
**[10:20]** pantic for getting structured outpours  
**[10:22]** and then of course light lm so that we  
**[10:25]** can switch between the LLMs that we wish  
**[10:28]** to and then we go forward with the  
**[10:30]** function to uh just get the embeddings  
**[10:33]** out of it. So whenever you you uh have  
**[10:36]** any any kind of uh document that you  
**[10:39]** want to ingest so just for reference we  
**[10:41]** are using a very simple PDF document to  
**[10:44]** to uh which is a financed uh which  
**[10:46]** explains finance terminologies. So it's  
**[10:49]** a very basic document for for sake of  
**[10:51]** simplicity and PC purpose we we try to  
**[10:53]** just show you what is possible. So we  
**[10:56]** define our embedding function here. Then  
**[10:58]** we go ahead and define the LLM that we  
**[11:01]** want to use. So so uh I I say we are GPU  
**[11:04]** GPU poor people. So we uh resort to uh  
**[11:08]** uh we resort to grock to provide us uh  
**[11:11]** the LLM and that the one that we are  
**[11:13]** using is llama 3.370 billion model and  
**[11:16]** then uh we we have our we have connected  
**[11:20]** it to our neo 4j instance that will have  
**[11:23]** the uh data once we upload it and then  
**[11:26]** uh we can go ahead and define what our  
**[11:29]** atomic facts is. So this is a class  
**[11:31]** where we define our atomic facts. So  
**[11:33]** essentially if you uh see saw what I uh  
**[11:36]** previously shared that atomic facts  
**[11:38]** would be the nouns, verbs and  
**[11:40]** essentially any real world entity that  
**[11:42]** you have and uh the sorry that is the  
**[11:45]** key element and the atomic fact would be  
**[11:47]** any any single indivisible fact as a  
**[11:50]** concise sentence. So anything that is  
**[11:52]** related to those entities will come as  
**[11:54]** an atomic fact and then uh we we uh  
**[11:58]** consider that our document is of a  
**[12:00]** unstructured uh nature and then we go  
**[12:03]** ahead and uh write how how you can  
**[12:06]** extract chunks. So we basically are  
**[12:09]** doing a chunk extraction here. So once  
**[12:12]** once uh you are uh you are ready to  
**[12:16]** ingest your document. So you uh  
**[12:18]** basically just uh say where where from  
**[12:20]** your chunking would be done. uh you just  
**[12:23]** uh write uh write how how you're uh you  
**[12:27]** just uh give the input to your uh  
**[12:29]** ingesting file that you have and then  
**[12:31]** you uh so we we went forward with a  
**[12:34]** section wise chunking uh which is  
**[12:36]** similar to what has been discussed in  
**[12:38]** the paper like a paragraph chunking and  
**[12:40]** then uh we we uh see how how the ele we  
**[12:44]** we leave it up to the LLM based on the  
**[12:46]** prompt that we had previously given to  
**[12:48]** extract the key atomic facts and chunks  
**[12:51]** uh key elements for  
**[12:53]** And uh we then uh create our index which  
**[12:57]** would uh save these uh save these chunks  
**[13:00]** after converting it to embeddings and  
**[13:02]** then uh it will be available uh to to  
**[13:05]** the um it will be available into into  
**[13:09]** the new 4j instance that you have. Uh so  
**[13:12]** so for testing purpose we just gave it  
**[13:14]** uh this this sent uh  
**[13:17]** these these uh four to five line  
**[13:19]** sentence to see how it works and and it  
**[13:22]** was able to uh ingest it up. So maybe I  
**[13:26]** can show you that uh how how it looks  
**[13:30]** like after ingestion.  
**[13:33]** Okay.  
**[13:36]** All right. Uh okay. Maybe I need to  
**[13:39]** reshare it again.  
**[13:42]** Let me do a full share.  
**[14:00]** All right. Uh okay. So this is my RDB  
**[14:03]** instance where my uh data has been  
**[14:05]** ingested and it has certain nodes of uh  
**[14:08]** entity nodes. uh if you if you hover  
**[14:10]** over you will see that uh it has  
**[14:12]** identified Tesla as a node and dollar  
**[14:14]** 25.7  
**[14:17]** billion and and so on and so forth as  
**[14:19]** the entity nodes and if you uh want to  
**[14:22]** do has entity uh these are the  
**[14:24]** relationships that will be captured uh  
**[14:27]** within the nodes and and this is just to  
**[14:29]** show you how you can visualize and uh  
**[14:32]** like there are other options if you want  
**[14:33]** to see the attached facts that are there  
**[14:36]** to the particular document then you can  
**[14:38]** traverse more to the graph. Uh, all  
**[14:41]** right, let's head back to our VS Code.  
**[14:52]** All right. Now, now that we have already  
**[14:55]** ingested our our system, we our our uh  
**[14:59]** we have already ingested and if you see  
**[15:00]** here also, we we tried to test it out  
**[15:02]** and see what exactly our atomic facts  
**[15:05]** are. it it also gives us here that what  
**[15:08]** exact atomic facts it has returned. So  
**[15:11]** now we are good to go with the retrieval  
**[15:13]** step. So this is where uh we we uh  
**[15:16]** install some more packages like neo 4j  
**[15:18]** graph rag and lang chain light lm um and  
**[15:24]** uh obviously lang graph for for uh  
**[15:26]** having the agentic nature. We also keep  
**[15:29]** uh lang lang graph checkpoint SQL so  
**[15:32]** that within the intermediate uh steps  
**[15:34]** you are able to uh store uh store the um  
**[15:38]** memory uh that uh the agent requires to  
**[15:41]** take the next steps. So we import our  
**[15:44]** libraries here. Again we we define the  
**[15:46]** uh sentence transformers and then uh we  
**[15:49]** can go ahead and uh obviously connect to  
**[15:52]** our DB instance uh define our LLM here  
**[15:56]** and then we uh try try to uh get to our  
**[16:00]** index and then uh we we uh define some  
**[16:04]** uh utility functions here that uh so  
**[16:06]** this is basically just to connect and if  
**[16:08]** the connection just fails what do you do  
**[16:10]** next? So here it returned a successful  
**[16:13]** connection and you have both indexes  
**[16:15]** like fact embeddings and section  
**[16:16]** embeddings. So uh in your retrieval uh  
**[16:20]** class you can basically define uh what  
**[16:23]** are the things that you will be needing.  
**[16:26]** You can uh keep you would first have the  
**[16:28]** user query and uh it sometimes can  
**[16:31]** happen that the user query is uh  
**[16:33]** modified to uh uh basically a query  
**[16:36]** rewriting happens which is more suitable  
**[16:38]** for the agent to go up and uh search for  
**[16:42]** it and what are the current nodes or the  
**[16:44]** facts that are extracted from that user  
**[16:46]** query. You would have a notebook or the  
**[16:49]** scratch pad per se which the agent  
**[16:51]** maintains on the steps it has to  
**[16:53]** implement and you have a traversal count  
**[16:55]** and traversal limit so that you uh won't  
**[16:57]** be uh like uh missing out uh you won't  
**[17:01]** run into the problems because of uh like  
**[17:04]** agentic systems have to make uh to make  
**[17:06]** the agentic system reliable and then you  
**[17:09]** go on with the uh langraph agent nodes  
**[17:13]** where you first uh so we we first  
**[17:16]** implemented using vector retriever which  
**[17:19]** uses uh the vector embeddings and and  
**[17:23]** the full text embeddings as well. Uh  
**[17:25]** later on we we have combine both of them  
**[17:28]** to get the best of both worlds. We  
**[17:30]** combine the vector embeddings plus the  
**[17:32]** so so the idea here is first it searches  
**[17:35]** the embeddings uh the the fact  
**[17:38]** embeddings index to get the exact  
**[17:40]** matches or similar matches. If it does  
**[17:43]** not find it there it then comes to the  
**[17:45]** uh section embeddings. So hopefully it  
**[17:47]** finds some some facts here. If it does  
**[17:49]** not even find it there then we are sure  
**[17:51]** that in the full text index it will  
**[17:53]** surely find the match and that's that's  
**[17:56]** a kind of full text index will work out  
**[17:58]** there and then you you go to your hop  
**[18:02]** analyzer which would um now traverse the  
**[18:06]** neighboring nodes. So once you have the  
**[18:08]** uh had the entity extracted the next  
**[18:10]** thing that you can do is you go on to uh  
**[18:12]** the neighboring nodes so that they have  
**[18:15]** related information which is more uh  
**[18:18]** suitable for for your uh graph  
**[18:20]** traversal. So you then uh extract the  
**[18:23]** neighboring nodes and then you get  
**[18:25]** information out of it. Uh so we we also  
**[18:27]** implemented a context manager here which  
**[18:30]** which uh basically maintains the uh so  
**[18:33]** that this this is a fallback mechanism  
**[18:35]** so that your LM doesn't run out of  
**[18:38]** context window uh and uh then uh you  
**[18:42]** have we also have an evaluate answer. So  
**[18:45]** it can be we we have to have an  
**[18:47]** evaluator. So we implemented a LLM as a  
**[18:50]** judge here so that it basically checks  
**[18:52]** three things. First  
**[18:56]** is whether uh at this stage after it has  
**[18:59]** hopped to my exact entity and the  
**[19:01]** neighbors it has the complete  
**[19:03]** information that it needs to present to  
**[19:04]** the user based on the user query. If it  
**[19:07]** is complete then this will proceed to  
**[19:09]** the LLM to give you out the final  
**[19:11]** answer. If not it will hop more. So it  
**[19:13]** will go on to more neighboring nodes and  
**[19:16]** more related entities or atomic facts to  
**[19:18]** extract more information uh to to get  
**[19:21]** related information. And if uh there is  
**[19:24]** a third step as well uh so deep dive so  
**[19:27]** uh say per say uh you whatever  
**[19:29]** information uh it got it is not uh  
**[19:32]** completely relevant to the uh user  
**[19:34]** query. So you might have to again go  
**[19:37]** back to a new node and traverse from  
**[19:39]** there. So these are the three kinds of  
**[19:42]** uh choices that you can make and then  
**[19:44]** you go to the u uh LLM to uh decide.  
**[19:48]** Finally, there is another uh fallback uh  
**[19:52]** that can happen here is that uh it  
**[19:55]** doesn't get any information at all and  
**[19:57]** then you basically have to uh this is  
**[20:00]** like the uh edge case where uh even uh  
**[20:03]** with the with the deep dive you have to  
**[20:05]** the the notebook or the scratch pad that  
**[20:08]** the agent maintains basically comes up  
**[20:10]** with with a plan retry mechanism and you  
**[20:13]** have to plan up again that whatever my  
**[20:16]** uh my uh system has so far extracted is  
**[20:19]** not correct and I need to again uh do a  
**[20:22]** query modification there. So all of this  
**[20:26]** uh happens and then finally you're able  
**[20:27]** to come up with an answer. So which  
**[20:29]** basically calls an LLM. It gives these  
**[20:32]** things to the LLM to the original  
**[20:35]** question that was asked the facts and  
**[20:37]** the actual scratch pad that it was  
**[20:39]** maintaining to get you the answer and  
**[20:41]** yeah so maybe whatever so far I was  
**[20:45]** talking about can be very well  
**[20:46]** visualized from here. So you start you  
**[20:49]** do a initial discovery you do your hop  
**[20:51]** analyzer you maintain a context manager  
**[20:54]** which uh tries to keep your LLM context  
**[20:58]** window limited and you evaluate the  
**[21:00]** three conditions that whether it is  
**[21:02]** sufficient or you need to hop more or  
**[21:04]** you need to deep dive. So if it is  
**[21:06]** sufficient it will get you the final  
**[21:08]** answer. If it is not it will hop more to  
**[21:10]** the neighboring nodes and if you need to  
**[21:12]** deep dive you need to again create a new  
**[21:15]** plan which is uh again you start with  
**[21:17]** the initial discovery stage. So uh this  
**[21:21]** is what we asked that what was Tesla's  
**[21:24]** revenue in Q4 and this is what it uh  
**[21:27]** basically gave us that it went for a  
**[21:29]** traversal count of zero and traversal  
**[21:31]** limit of three and it had hit these  
**[21:34]** these uh vector hits. So uh there were  
**[21:37]** three conditions if you remember we we  
**[21:39]** discussed that uh first one was uh  
**[21:42]** either it gets the embeddings or it gets  
**[21:45]** the uh full text index and lucky or the  
**[21:49]** either the fact embeddings or the  
**[21:51]** section embeddings or the full text. So  
**[21:53]** it has very well got the match the  
**[21:55]** vector embeddings as in the first place  
**[21:58]** and these were the current nodes that it  
**[21:59]** explored and this is the final answer  
**[22:01]** that it produced. So this is uh  
**[22:04]** basically the the entire uh flow that we  
**[22:07]** had in mind to implement and u  
**[22:10]** unfortunately Sia is not able to share  
**[22:12]** or he's having some technical issues. We  
**[22:15]** we did some more u way u some next steps  
**[22:18]** as well to this uh it would have been  
**[22:20]** great if he could come but we have  
**[22:22]** linked everything we will be sharing the  
**[22:24]** slides and this whole notebook for your  
**[22:26]** reference and you can go through that as  
**[22:28]** well. Uh, all right. Let me get back to  
**[22:32]** my slides now. And as we are running  
**[22:36]** short of time, we need to wrap up.  
**[22:39]** Okay.  
**[22:47]** All right. Um,  
**[22:51]** not this one.  
**[23:04]** Okay. Uh  
**[23:11]** so um certain certain things that uh we  
**[23:14]** wish to cover is that uh there are  
**[23:16]** certain limitations to the to the  
**[23:18]** implementation we did. Uh  
**[23:23]** oh okay sorry about that. So so uh we we  
**[23:28]** uh have not considered compute  
**[23:31]** challenges that you can maybe run into.  
**[23:33]** So when when you are implementing into  
**[23:36]** production uh there will be large amount  
**[23:38]** of data and you will need more time to  
**[23:40]** uh in the injection process as well as  
**[23:42]** the retrieval process. It will be  
**[23:44]** something that consumes greater uh  
**[23:47]** compute. you can maybe uh think of some  
**[23:50]** optimization techniques that we are  
**[23:52]** trying to currently come up with. So if  
**[23:54]** you remember in the  
**[23:57]** in the extraction phase we were going  
**[23:59]** during the retrieval phase we were going  
**[24:01]** into three types of indexes. So if  
**[24:03]** possible we can do that in parallel as  
**[24:05]** well and then give a weighted weighted  
**[24:07]** average and have the fusion of it to  
**[24:10]** answer at the final. This can be one  
**[24:12]** step and another thing that we can run  
**[24:15]** into is is the uh non-deterministic  
**[24:18]** nature of LLMs is is uh a problem where  
**[24:21]** you might miss out on certain  
**[24:23]** information because uh you are leaving  
**[24:25]** the LLM to uh construct the entire  
**[24:28]** schema for you, entire ontology for you.  
**[24:30]** So these these minor problems can be  
**[24:32]** that it sometimes misses out on the  
**[24:35]** broader information that you really want  
**[24:37]** to do. Uh another thing that that we are  
**[24:40]** trying to implement is is uh undirected  
**[24:43]** or no no so basically here the path that  
**[24:47]** we took was a kind of directed one. So  
**[24:50]** we are instructing the LLM on how to  
**[24:52]** think on how which nodes to go. Can we  
**[24:55]** do it in a undirected way so that it is  
**[24:57]** up to the judgment of the agent that  
**[25:00]** where it needs to go and how it needs to  
**[25:02]** traverse and dynamically it comes up  
**[25:04]** with a more better uh solution there. So  
**[25:08]** these these are kind of uh some some  
**[25:10]** more things that we are exploring and uh  
**[25:12]** feel free so so it's all open sourced we  
**[25:14]** we have linked our u so you can maybe  
**[25:18]** scan this to get access to our slides  
**[25:20]** and this is the code repository that we  
**[25:23]** have and feel free to uh maybe uh make a  
**[25:26]** contribution or uh help us with  
**[25:28]** suggestions on what your your take on it  
**[25:30]** is and uh we we this is a original paper  
**[25:34]** that we followed graph reader paper And  
**[25:37]** uh there is an excellent uh blog as well  
**[25:39]** by Traumas Branic. He he's from Neo4j.  
**[25:42]** He has written a very excellent blog on  
**[25:44]** how he has implemented it. So so uh do  
**[25:47]** do keep exploring and uh help us with  
**[25:50]** your suggestions and anything that you  
**[25:51]** have. Uh thank you for your time for  
**[25:53]** hearing us out and if there is time we  
**[25:55]** can take some questions or or reach us  
**[25:57]** on socials to u bug us with questions.  
**[26:14]** All right. Uh, are there any questions?  
**[26:17]** I see we have 3 minutes left.  
**[26:23]** Let me go through the comments.  
**[26:28]** Okay, let me paste the link as well for  
**[26:31]** anyone  
**[26:33]** wants to go through can can uh  
**[26:37]** just refer to this  
**[26:56]** And maybe I can put down our socials as  
**[26:59]** well for my social as well as Somia's  
**[27:01]** social. So you can reach out to us at  
**[27:03]** any point and uh ask us questions  
**[27:08]** or give us suggestions on what you think  
**[27:11]** could be done next.  