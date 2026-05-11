# Transcript: https://www.youtube.com/watch?v=bxXb8oT5E-k

**Language:** English (auto-generated) (en) — auto-generated
**Snippets:** 655

---

**[00:03]** [music]  
**[00:08]** Um hey everybody how's it going? Thank  
**[00:10]** you so much for being here. Uh today I  
**[00:13]** want to talk to you about a aentic graph  
**[00:15]** rag. Uh more specifically a multi- aent  
**[00:18]** approach of creating knowledge graphs.  
**[00:21]** This is something that my team and I  
**[00:22]** have developed as a workflow uh because  
**[00:25]** we've been doing a lot of research and a  
**[00:27]** lot of uh team members are storing their  
**[00:30]** data across you know cloud folders and  
**[00:32]** in their own personal folders and there  
**[00:34]** was no way for us to find the data and  
**[00:36]** look at what we researching and so this  
**[00:39]** tool is something that we've created and  
**[00:41]** it's obviously evolving as we speak but  
**[00:43]** I wanted to share this with you uh get  
**[00:46]** your thoughts on it and you know  
**[00:47]** hopefully you can also implement this  
**[00:48]** within your teams as  
**[00:51]** So today's agenda I want to talk to you  
**[00:53]** about the current challenge that we're  
**[00:54]** facing the architecture overview um with  
**[00:58]** the data extraction strategies and  
**[01:00]** what's next because I think this is like  
**[01:03]** version two version two in this whole  
**[01:05]** app dev that we're doing and so this is  
**[01:08]** adding to like a broader vision  
**[01:10]** internally for our team and that's what  
**[01:12]** happens that's what I want to talk to  
**[01:14]** you about in what's next. So before we  
**[01:18]** begin, I always like to start off the  
**[01:19]** presentation by this famous quote by Fei  
**[01:22]** Lee. Artificial intelligence is not a  
**[01:24]** substitute for human intelligence. It is  
**[01:27]** a tool to amplify human creativity and  
**[01:30]** ingenuity. And this is something that I  
**[01:32]** always go back to as an anchor because  
**[01:35]** yes, AI is cool, but if it doesn't help  
**[01:38]** us do a uh improve our workflows or make  
**[01:41]** us more efficient, I feel like it's it's  
**[01:44]** it wouldn't be of no use to us, right?  
**[01:46]** So this is almost like a grounding  
**[01:47]** anchor.  
**[01:49]** Okay. So let's look at the current  
**[01:50]** challenge that this is again that's this  
**[01:53]** is what we're facing and I'm sure  
**[01:55]** different teams have different kinds of  
**[01:56]** problems that they're facing but this is  
**[01:58]** internal to us. And so the first one is  
**[02:00]** unstructured data right fragmented  
**[02:02]** storage. All of the research data lives  
**[02:05]** across multiple cloud folders and  
**[02:07]** personal drives. Uh scattered notes. the  
**[02:10]** every researcher adds notes based off  
**[02:12]** the data that they've seen but they live  
**[02:14]** in that particular folder and so the  
**[02:16]** valuable insights kind of get buried uh  
**[02:19]** redundant effort and so if one team  
**[02:22]** member does some kind of research but  
**[02:24]** then the other team member would have to  
**[02:25]** look at the nodes and may also have to  
**[02:27]** look at the data so you're kind of you  
**[02:29]** know duplicating the work over and over  
**[02:30]** again and also disconnected context uh  
**[02:34]** notes and datas are not linked together  
**[02:36]** and so it's hard to find which of the  
**[02:39]** research paper that the notes were made  
**[02:41]** from.  
**[02:43]** So just to give an example like every  
**[02:45]** researcher uploads and again this is  
**[02:48]** internally right. So we my team uh the  
**[02:51]** researcher uploads the data sets and  
**[02:53]** notes into separate folders and so as a  
**[02:56]** result of which the insights kind of  
**[02:58]** tied to the individual files stay tied  
**[03:01]** to the individual files and this makes  
**[03:03]** it difficult to connect the findings and  
**[03:05]** also to trace a single idea. you might  
**[03:07]** you almost have to go back through  
**[03:09]** multiple different research papers that  
**[03:11]** we would have read and not just research  
**[03:13]** papers you know like Excel files data  
**[03:15]** sets that we have we would have  
**[03:16]** initially combed through to get to this  
**[03:18]** point in the first place and and so when  
**[03:22]** every and and even though every  
**[03:24]** researcher would find relevant data but  
**[03:26]** they would save it in separate folders  
**[03:28]** just so they're trying to organize this  
**[03:30]** whole thing and so the notes and  
**[03:32]** observations are kind of stored in the  
**[03:34]** same folder as the data  
**[03:36]** and and over time each folder becomes  
**[03:39]** its own mini knowledge base because  
**[03:41]** you're kind of adding more notes to the  
**[03:43]** same folder and so when the team meets  
**[03:46]** uh we discuss findings but the insights  
**[03:49]** kind of remain scattered across the  
**[03:51]** folders and so this is the current this  
**[03:53]** is the challenge that we were facing  
**[03:55]** when we started this whole process. uh  
**[03:58]** let's look at what the architecture that  
**[03:59]** we're proposing and so the architecture  
**[04:02]** that we're proposing and this is the  
**[04:04]** core of what we're proposing is we start  
**[04:06]** with user uploaded PDFs and it can be  
**[04:08]** any kind of data set you know PDFs  
**[04:10]** research papers uh you know Excel files  
**[04:13]** JSON tables JSON formatted tables you  
**[04:16]** know any kind of data set uh and that is  
**[04:19]** put through the pipeline and that's this  
**[04:21]** is the multi- aent pipeline where we  
**[04:22]** have four agents and one agent  
**[04:26]** identifies ies entities and  
**[04:28]** relationships. Uh the second one kind of  
**[04:30]** extracts uh the entities and  
**[04:32]** relationships from the data. Uh the  
**[04:35]** third one merges them because you know  
**[04:37]** sometimes we have duplicates when we are  
**[04:39]** kind of chunking the data across the  
**[04:41]** board. And finally the fourth one is a  
**[04:44]** QC check which kind of optimizes the  
**[04:47]** graph before then being pushed to Neo4j  
**[04:50]** for persistence. And finally, all of  
**[04:53]** this is connected to a chatbot. And in  
**[04:56]** our case, we try we use the latest um  
**[04:59]** OpenAI's chat kit with the help of um  
**[05:02]** Neoforj's MCP server to then help us  
**[05:06]** query the database based on the research  
**[05:08]** that we're doing. So this is uh an  
**[05:11]** overview of what we are using in our app  
**[05:14]** at least and that's what we're  
**[05:15]** proposing. In terms of the text stack,  
**[05:18]** uh this is this being a web app. We use  
**[05:20]** NexJS and TypeScript with Tailwind CSS  
**[05:23]** and Shhatzy and UI. The AI layer is  
**[05:26]** GPD5. Oh, before that I almost forgot.  
**[05:30]** Uh all of the multi- aents is is also  
**[05:33]** wrapped with lang tracing. So any kind  
**[05:36]** of agent that any kind of step that  
**[05:39]** takes that is taken by by an agent, we  
**[05:42]** can evaluate [clears throat] it on the  
**[05:44]** back end with the help of Lagsmith. So  
**[05:46]** that way um that way we can control the  
**[05:49]** output based on the input that's coming  
**[05:52]** in maybe change the prompts of each of  
**[05:54]** the agents to help fine-tune it better.  
**[05:57]** And so all of this is uh wrapped with  
**[05:59]** lang tracing  
**[06:02]** and and so the data layer in the text  
**[06:04]** stack is Neo4j.  
**[06:06]** So now that we've looked at the current  
**[06:08]** challenge and we've looked at the  
**[06:10]** architecture that we're proposing, let's  
**[06:12]** uh dig a little bit deeper, right? Let's  
**[06:14]** look at the solution. So this is how the  
**[06:17]** web app looks like for us wherein you  
**[06:20]** have uh wherein the researchers can drop  
**[06:23]** in their PDFs of any kind of data sets.  
**[06:25]** They can either define what they're  
**[06:27]** studying to get an AI suggested list of  
**[06:30]** entities and relationships or we can or  
**[06:33]** the user can define their own entities  
**[06:35]** and relationships that they want to that  
**[06:38]** they want the agents to look for in the  
**[06:40]** data. uh and then finally you can  
**[06:43]** process this and then the after which we  
**[06:46]** can look at what the graph looks like on  
**[06:49]** Neo4j.  
**[06:51]** So the first step in this whole process  
**[06:53]** is user input. In this the researchers  
**[06:56]** uploads the documents or data sets into  
**[06:58]** the system. uh they define what kind of  
**[07:01]** information that they want to extract  
**[07:03]** entities concepts right uh or  
**[07:05]** relationships and AI and so there so  
**[07:08]** there are two options that we added into  
**[07:10]** this whole thing which is one we as a  
**[07:13]** user can define the entities and  
**[07:15]** relationships that we're looking for or  
**[07:18]** we can you know define the area of  
**[07:20]** research and give it to the AI analyzer  
**[07:23]** which will then suggest some nodes and  
**[07:26]** entities  
**[07:27]** but the first step starts with adding  
**[07:29]** database adding data to the database. So  
**[07:32]** the idea is that the more we do research  
**[07:35]** on a particular domain and the more data  
**[07:38]** we accumulate all of that can be dropped  
**[07:41]** into this particular web app and so the  
**[07:43]** graph keeps expanding based on what  
**[07:45]** we're researching. So they're all living  
**[07:48]** in one location.  
**[07:51]** So the a one of the agents and the first  
**[07:54]** agent is an analyzer agent which is when  
**[07:58]** the user puts the PDF or the any data  
**[08:00]** set inside they can either rely on what  
**[08:04]** the agent thinks should be the entities  
**[08:06]** and relationships. So they can put in  
**[08:08]** what the research focus focuses and get  
**[08:11]** AI suggestions. uh in this there were  
**[08:14]** there were two ways or two directions  
**[08:16]** that we could have gone in this  
**[08:18]** particular uh in this particular agentic  
**[08:20]** approach was we could have taken the  
**[08:23]** data that's been uploaded by the user  
**[08:27]** and then taken the suggestion uh taken  
**[08:29]** the research focus and then made the AI  
**[08:32]** to compare like look into the data and  
**[08:34]** then suggest the LMS but we felt that  
**[08:37]** was a little bit redundant just in this  
**[08:40]** uh initial versions of the app. So what  
**[08:42]** we're doing in this case is just we're  
**[08:44]** just defining the uh research focus or  
**[08:47]** the area of focus that we're looking  
**[08:48]** into and based off of that you have the  
**[08:51]** LM that or the agent that is uh you know  
**[08:54]** suggesting entities and relationships.  
**[08:57]** So in this case you can tell that this  
**[09:00]** for anam for an example I put in the  
**[09:04]** latest uh research paper that was  
**[09:06]** released by Apple on the and that was  
**[09:09]** called the pico banana 400k and so I  
**[09:13]** asked AI to suggest some entities and  
**[09:15]** relationships and you can see on the  
**[09:17]** right you have the entity types and you  
**[09:20]** have the relationship types and all we  
**[09:22]** have to do is select which ones we want  
**[09:24]** or we can also add custom entity types  
**[09:26]** and relationships at the bottom.  
**[09:29]** >> So now that we have you know put in the  
**[09:32]** data and then we have also gotten the  
**[09:35]** entity types and relationships some of  
**[09:37]** them are suggested by AI some you know  
**[09:40]** by the user we go on to the next step  
**[09:42]** which is oh before that uh just to give  
**[09:46]** a idea or just to give a code snippet of  
**[09:49]** what the agent looks like. So we're we  
**[09:52]** we're doing the passing um function for  
**[09:55]** the open AIS API where the output is  
**[09:58]** going to be a JSON output and that is  
**[10:01]** obviously that is defined with Z. So  
**[10:04]** agent one analyzes the research focus  
**[10:07]** and suggest domain specific entry and  
**[10:09]** relationship types. Uh the researchers  
**[10:11]** can then select modify or add any kinds  
**[10:14]** of new entities and relationships. Uh  
**[10:16]** some of the examples for this particular  
**[10:19]** research paper was image edit  
**[10:21]** instruction data set subset and the  
**[10:24]** relationships was has edit instructions  
**[10:26]** are generated by this is just an example  
**[10:29]** uh use case but obviously you can add  
**[10:31]** your own um entities and relationships  
**[10:36]** um to and then we al like I mentioned  
**[10:38]** earlier we have lang tracing for eval so  
**[10:42]** every agent  
**[10:44]** behavior is fully observable through  
**[10:45]** lang web we can trace every LM call from  
**[10:49]** the system and the user prompts to the  
**[10:51]** structured response along with runtime  
**[10:53]** metrics. So this kind of helps us  
**[10:55]** validate the [snorts] accuracy, compare  
**[10:58]** prompt iterations and ensure the  
**[11:00]** pipeline stays consistent as we scale  
**[11:02]** across different research areas. Right?  
**[11:05]** So as you can tell with the image on the  
**[11:08]** right, that is the um that is the  
**[11:11]** backend eval that we looking at. And so  
**[11:14]** the output B it also gives you reasoning  
**[11:17]** and that's based on the ZOD kind of  
**[11:18]** definition that we put in. So we wanted  
**[11:21]** entities, we wanted relationships and  
**[11:23]** also we wanted the reasoning as to why  
**[11:26]** this was used, why these were selected  
**[11:28]** from that particular area of research.  
**[11:31]** Again just as to eval so that if we  
**[11:34]** don't like the way it's been done, we  
**[11:36]** can go back in and change the prompts  
**[11:39]** and you know look at it again.  
**[11:42]** So, so now we have put in the data. Uh,  
**[11:46]** we've chosen the entities and  
**[11:47]** relationships. We've also used the one  
**[11:50]** of the agent ones analyzer to give us  
**[11:52]** some examples and ideas of what we  
**[11:54]** should also look for look in the data  
**[11:57]** set for.  
**[11:59]** So the next agent is the extractor agent  
**[12:02]** which wherein we take the documents we  
**[12:05]** chunk them and then we compare the  
**[12:07]** entity types that we have chosen in step  
**[12:10]** one to what is present in all of these  
**[12:13]** in in the research paper. I'll tell you  
**[12:15]** more about it. So in this agent  
**[12:18]** essentially splits each document into  
**[12:20]** smaller check text  
**[12:22]** chunks for parallel processing. uh so it  
**[12:26]** applies the schema suggested by agent  
**[12:28]** one or you know the custom schema that  
**[12:31]** the user suggested and extracts  
**[12:33]** information from each chunk  
**[12:34]** independently and simultaneously. So all  
**[12:36]** of these chunks are being processed  
**[12:38]** parallelly and so this produces a  
**[12:40]** structured output of entities and  
**[12:42]** relationships from each chunk.  
**[12:46]** And what that means is uh so in the  
**[12:49]** first in the first step we selected  
**[12:51]** these were the selected nodes right  
**[12:53]** image edit instruction edit pair and  
**[12:55]** edit operation type and some of the  
**[12:57]** relationships that were that came out of  
**[12:59]** a step one with agent one was has edit  
**[13:03]** instruction has edit type um and also  
**[13:08]** part of so now it essentially takes the  
**[13:11]** chunks in this case the PDF that I put  
**[13:14]** in the research paper was divided it  
**[13:16]** into five chunks of 8,000 characters and  
**[13:19]** it takes each chunk and then finds out  
**[13:22]** the note with the type. So for example  
**[13:24]** on the right side you can see with it it  
**[13:27]** found out the ID uh the type is edit  
**[13:30]** instruction and the properties. So it's  
**[13:32]** essentially taking the type uh the  
**[13:35]** entity type that we want to look for and  
**[13:37]** it's finding similar content and it's  
**[13:40]** creating a node out of it. And same  
**[13:42]** thing with relationships. It took the  
**[13:44]** relationship in this case the type is  
**[13:46]** has edit instruction and it found the  
**[13:48]** target found the source and it found the  
**[13:51]** properties. So essentially we're kind of  
**[13:53]** finding we're creating relationships and  
**[13:55]** also entities around the around our  
**[13:59]** entities and relationships that we want  
**[14:01]** to based off that we want to find that  
**[14:05]** we want to research based off our area  
**[14:07]** of focus.  
**[14:10]** Um and so the co the code snippet for  
**[14:13]** this a for this agent is uh essentially  
**[14:16]** this wherein the GPD5 extracts entities  
**[14:19]** and relationships. Uh [clears throat]  
**[14:20]** another thing that in the code as you  
**[14:22]** can tell this entire agent is wrapped  
**[14:25]** with a traceable function and that's how  
**[14:27]** we can you know trace all of these  
**[14:30]** agentic agentic steps that it takes  
**[14:32]** every single time. Um and so the prompts  
**[14:36]** and the model with strict guidelines to  
**[14:38]** minimize duplicates output structured  
**[14:41]** objects notes to entities uh  
**[14:44]** relationships links between entities  
**[14:48]** and so this is the example of this  
**[14:50]** agent's uh evaluation that's happening  
**[14:53]** in the back end. So we can debug each  
**[14:55]** process chunk to confirm that the  
**[14:57]** correct nodes and relationships were uh  
**[15:00]** relationships were  
**[15:03]** relationships were extracted. Uh we  
**[15:05]** [snorts] can validate the properties and  
**[15:06]** the types of each entity directly from  
**[15:08]** the trace output and it provides full  
**[15:10]** visibility into each LLM's call  
**[15:13]** including the input text, the schema and  
**[15:16]** the output. as and as you can tell in  
**[15:18]** the image we have I think this is we are  
**[15:20]** looking at um we're looking at  
**[15:23]** relationships in this case and so you  
**[15:25]** have the source you have the target you  
**[15:27]** have the relationship type and you have  
**[15:29]** a little bit of a description to give us  
**[15:31]** the context of what this uh whole whole  
**[15:34]** entity and relationship was. [snorts] So  
**[15:37]** now that we've gone through five uh five  
**[15:40]** chunks and which this kind of gives  
**[15:43]** about similar entities and relationships  
**[15:47]** across each chunk but now we want to  
**[15:49]** kind of merge them obviously with  
**[15:51]** reasoning but also merge them to remove  
**[15:54]** dup any kind of duplicates and  
**[15:56]** consolidate the whole list. And that  
**[15:58]** happens with the entity merger that  
**[16:01]** happens with the entity merger  
**[16:02]** [clears throat] agent. And so in this  
**[16:03]** case in this the agent consolidates any  
**[16:06]** kind of duplicate entities using LLM  
**[16:09]** based resing  
**[16:11]** instead of string matching. So we're  
**[16:13]** just not matching the text of the input  
**[16:16]** schema uh text of the entities and  
**[16:19]** relationship across the five chunks. We  
**[16:21]** are essentially taking the description  
**[16:23]** that it came with that it comes with and  
**[16:26]** the LM is essentially reasoning as to  
**[16:28]** see if they both are along the same  
**[16:30]** lines. If yes then they're merged. So  
**[16:33]** from these from the five chunks we got  
**[16:36]** about 84 entities. Uh just to give an  
**[16:38]** example edit instructions you had AC++  
**[16:42]** instruct picks to pix and instruct edit  
**[16:45]** edit pairs  
**[16:48]** uh and also edit operation type. So like  
**[16:50]** these had almost similar reasoning and  
**[16:53]** so it kind of you know merged all of  
**[16:56]** these. it merged whatever it thought was  
**[16:59]** similar and it came down to 32  
**[17:02]** dduplicated entities.  
**[17:05]** Uh just to give an example and to give  
**[17:07]** an example of what the code looks like  
**[17:08]** again this is also wrapped with a  
**[17:11]** traceable function from languid and so  
**[17:13]** it groups all the extracted entities by  
**[17:16]** type and each group is then sent to the  
**[17:19]** agent to do semantic dduplication based  
**[17:22]** on meaning and formality.  
**[17:24]** uh the LLM also identify variations that  
**[17:27]** refer to the same real world entity and  
**[17:30]** it maps duplicate names to a canonical  
**[17:34]** entity name right and all  
**[17:35]** [clears throat] of this gets is defined  
**[17:37]** in this um in the with the within the  
**[17:40]** agent as an instruction and finally this  
**[17:43]** is what the lang tracing looks like and  
**[17:46]** so the trace shows how agent 3 merged  
**[17:48]** all the duplicate entities now we can  
**[17:51]** now open any merge call that has  
**[17:53]** happened review the raw inputs and the  
**[17:55]** canonical outputs and even read the  
**[17:58]** LLM's reasoning as to why these entities  
**[18:01]** were combined and the reasoning again is  
**[18:04]** obtained based off of the ZOD schema  
**[18:07]** that we have defined. Uh because again  
**[18:10]** we want to know we want to eval and  
**[18:13]** another thing that I forgot to um  
**[18:16]** explain before was in this whole process  
**[18:19]** of building this solution for our team.  
**[18:21]** I think eval was the top priority.  
**[18:26]** Yes, we could have built without it, but  
**[18:29]** without having any kinds of eval, the  
**[18:31]** research team couldn't have actually  
**[18:33]** looked at how good the output was and  
**[18:36]** compared it to what their output was  
**[18:38]** when they did it without this app before  
**[18:41]** when the app existed. So, Eval is I feel  
**[18:43]** like the bedrock of any uh AI solution  
**[18:46]** that is that needs to be built out  
**[18:48]** there.  
**[18:50]** And so now we've gone through the four  
**[18:52]** agents, right? The three agents and then  
**[18:55]** the fourth agent and the final one is an  
**[18:57]** optimizer which essentially validates  
**[19:00]** and optimizes the graph quality.  
**[19:03]** So agent 4 is a semantic QA quality  
**[19:06]** assessment pass. It removes three  
**[19:09]** relationships. It in this case it  
**[19:11]** removed three relationships that were  
**[19:13]** either reversed or were using the wrong  
**[19:15]** word. So it kind of looks at grammatical  
**[19:17]** errors. It looks at the description. It  
**[19:20]** looks at everything and finds  
**[19:22]** similarities and and suggests that these  
**[19:25]** things need to be removed because you  
**[19:27]** know uh it has its own set of reasoning.  
**[19:29]** And so for example in this particular  
**[19:32]** run that we did it removed three  
**[19:34]** relationships which is Gemini's 2.5 Pro  
**[19:37]** produced by model and nano banana. It  
**[19:40]** was likely redundant and the reasoning  
**[19:42]** is is what it says was likely reversed  
**[19:44]** or redundant. evaluation is not equal to  
**[19:47]** production. Then nanobanana applies edit  
**[19:50]** operation to an MLM based quality  
**[19:53]** scoring. This is a semantic mismatch.  
**[19:56]** Quality scoring is an assessment method,  
**[19:59]** not an edit op. So I don't know if you  
**[20:01]** remember in the beginning we wanted to  
**[20:04]** look for ederit uh operations and so it  
**[20:08]** it still took the initial entities and  
**[20:10]** relationships that we defined and it's  
**[20:13]** you know bringing into this and then uh  
**[20:15]** optimizing this even more based off of  
**[20:17]** our initial  
**[20:20]** [clears throat] entities and  
**[20:21]** relationships that we've defined. Uh and  
**[20:23]** so the last one was and only  
**[20:25]** relationships were removed. None of the  
**[20:27]** nodes were removed in this whole  
**[20:28]** process.  
**[20:31]** So agent 4 is essentially the graph  
**[20:34]** quality auditor. It samples parts of the  
**[20:36]** graph, asks the GPD, asks the agent to  
**[20:40]** flag vague or inconsistent relationships  
**[20:42]** in comparison to the defined entities  
**[20:46]** and relationships from step one and  
**[20:48]** removes only those with lower  
**[20:49]** confidence.  
**[20:51]** >> [clears throat]  
**[20:51]** >> Uh the goal is to not delete data but to  
**[20:54]** improve semantic precision keeping the  
**[20:56]** final graph lean and meaningful before  
**[20:59]** saving it to neoforj.  
**[21:03]** Um so again this is also wrapped with  
**[21:06]** the langid traceable and so in this we  
**[21:09]** can look at the trace for the final  
**[21:12]** event. So every optimization call is  
**[21:15]** recorded including what data was sampled  
**[21:17]** and what issues were flagged and the  
**[21:20]** reasoning behind each decision. So this  
**[21:22]** means every relationship removal or node  
**[21:26]** adjustment can be traced, reviewed and  
**[21:29]** even replayed and that's the beauty of  
**[21:31]** [snorts] Langmith. So the level of  
**[21:33]** transparency gives us the confidence  
**[21:35]** that based on what research papers or  
**[21:39]** research data we put in based on what  
**[21:42]** entities and relationships we define  
**[21:44]** that the output  
**[21:47]** that came about was what we needed and  
**[21:51]** and I'm not saying it's 100% accurate  
**[21:53]** always but with the help of evals and  
**[21:56]** you know us fine-tuning the prompt for  
**[21:59]** each of the agents it kind of gets gets  
**[22:02]** us closer to being 100%. We only need a  
**[22:05]** little bit of, you know, little bit of  
**[22:07]** time and effort in the end to now  
**[22:09]** massage the research that we're doing.  
**[22:11]** And that's that's all possible. was only  
**[22:13]** possible with the help of Lang Smith's  
**[22:17]** evals  
**[22:19]** [snorts] and  
**[22:22]** yeah  
**[22:24]** so once once we've once we've you know  
**[22:28]** gone through all the bases which is  
**[22:29]** starting with the whole PDF entities and  
**[22:32]** pushing it through [clears throat]  
**[22:34]** all the four agents we finally have to  
**[22:37]** push it to Neo4j for persistence and so  
**[22:40]** in this case  
**[22:42]** everything we extracted is cleaned and  
**[22:44]** then it's written into the Neo4j  
**[22:47]** database. Uh in this case we've used the  
**[22:50]** batch unwind pattern. One query creates  
**[22:53]** all nodes and other groups with  
**[22:56]** relationships by type. So this kind of  
**[22:59]** is almost 10 times faster than the  
**[23:01]** standard inserts uh thanks to merge and  
**[23:04]** flexible enough to handle the dynamic  
**[23:07]** schema definitions.  
**[23:09]** So just in this particular example the  
**[23:13]** [clears throat] write time was about 2  
**[23:14]** seconds. Uh total the there were about  
**[23:18]** 57 nodes that were put in 179  
**[23:20]** relationships four distinct relationship  
**[23:23]** types for each of those nodes. Uh the  
**[23:26]** right pattern was like I mentioned batch  
**[23:28]** unwind plus merge and it was  
**[23:30]** successfully stored  
**[23:32]** to neoforj. So and each relationship  
**[23:35]** type is also grouped for performance. So  
**[23:37]** that makes it faster while while in this  
**[23:40]** whole process.  
**[23:43]** Um so just to give an example of what  
**[23:46]** the code looks like for this for this  
**[23:48]** final step is it writes all the nodes  
**[23:51]** and relationships to Neo4j when uh in  
**[23:53]** batch using the unwind plus merge but  
**[23:56]** merge pattern groups relationships by  
**[23:58]** types and this is the types uh that we  
**[24:01]** we had you know uh we had put it in the  
**[24:05]** put in the step one entities and  
**[24:08]** relationships. So those are those are  
**[24:10]** called those are what we define as types  
**[24:12]** and based off of the types it's it you  
**[24:15]** know groups the relationships and  
**[24:16]** entities and then pushes it into  
**[24:19]** neoforj.  
**[24:21]** Uh each relationship type is written in  
**[24:23]** its own cipher query for like parallel  
**[24:25]** efficiency  
**[24:26]** and [clears throat] automatically  
**[24:28]** sanitizes user defined relationship  
**[24:30]** names. So like uppercase special special  
**[24:32]** characters and also are replaced. And so  
**[24:37]** now this kind of gives us the  
**[24:39]** opportunity to then use cipher query  
**[24:41]** from the chatkit or any chatbot with the  
**[24:44]** help of MCP server for us to query all  
**[24:46]** of the data and the research that we've  
**[24:49]** done. And the final step is you know we  
**[24:53]** kind of hook it up to the chat kit with  
**[24:57]** the help of Neoforj's MCP server and  
**[25:01]** that's how um and then we start asking  
**[25:04]** questions. So essentially what we've  
**[25:07]** created is our version of a internal  
**[25:11]** assistant that just takes all the data  
**[25:14]** in but not all the data from the  
**[25:16]** internet more so um the data that we  
**[25:20]** deem necessary for a particular research  
**[25:22]** that we're doing. So this instant kind  
**[25:25]** of uh exists for different types of  
**[25:27]** research that happens in different  
**[25:29]** domains.  
**[25:31]** So what's next? So what's next? We have  
**[25:35]** a couple of steps that we're looking to  
**[25:37]** help improve this process even better is  
**[25:41]** domain agnostic. The same work uh work  
**[25:43]** the same architecture works across any  
**[25:46]** research domain and that I think comes  
**[25:48]** from kind of looking at the types of um  
**[25:52]** looking at types of prompts and how can  
**[25:55]** we make the prompts better. But that's  
**[25:57]** just step one. I think step two is also  
**[26:00]** injecting while it's analyzing while the  
**[26:04]** agents are doing injecting some  
**[26:06]** instructions  
**[26:08]** similar to how clot code has come up  
**[26:10]** with their skills.m MD. So this is  
**[26:13]** another step that we are planning to add  
**[26:15]** wherein each agent has its own version  
**[26:18]** of rag which it can then look at look at  
**[26:20]** the things that it needs to dig into and  
**[26:23]** then does the you know entity extraction  
**[26:27]** merging and optimizing  
**[26:30]** uh graph analytics I don't think we've  
**[26:32]** pushed how much of neoforj is being used  
**[26:34]** in this uh for now it's it's a great way  
**[26:37]** to build the knowledge graph but I think  
**[26:40]** we want to push it more in terms terms  
**[26:42]** of data science, algos,  
**[26:45]** page ranking, community deduction, uh  
**[26:48]** link prediction and similarities across  
**[26:51]** the nodes and relationships.  
**[26:53]** Uh multimodal extraction, that's a big  
**[26:55]** thing that we're looking into. Right  
**[26:57]** now, [clears throat] it just does text  
**[27:00]** and a little bit of tables, right? But  
**[27:02]** we want to be able to bring in images,  
**[27:04]** videos and uh and make it multimodal in  
**[27:07]** terms of extracting the data u and so  
**[27:10]** and also real-time pipeline. This is  
**[27:13]** real time to a certain extent, but  
**[27:17]** we want to give this uh we want to give  
**[27:20]** this workflow the ability to just keep  
**[27:22]** ingesting not just the not just the  
**[27:24]** people or the users putting in the data  
**[27:26]** but also while we're quering we can do a  
**[27:29]** query onto the internet and that data  
**[27:31]** goes in as well and the graph just keeps  
**[27:34]** updating based on the guardrails that we  
**[27:37]** have [snorts]  
**[27:38]** uh defined going  
**[27:41]** Um, and so I want to end this and if you  
**[27:45]** have any questions, please uh  
**[27:50]** [music]  