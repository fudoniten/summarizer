#!/usr/bin/env python3

import argparse
import os
import sys

import ollama

from langchain.chains.summarize import load_summarize_chain
from langchain.prompts import PromptTemplate
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.callbacks.base import BaseCallbackHandler
from langchain_community.document_loaders import TextLoader
from langchain_community.llms import Ollama


class PrintProgressCallback(BaseCallbackHandler):
    def on_chain_start(self, serialized, inputs, **kwargs):
        print(f"🔄 Starting summarization chain...")

    def on_chain_end(self, outputs, **kwargs):
        print(f"✅ Summarization complete.")

    def on_llm_start(self, serialized, prompts, **kwargs):
        print(f"📝 Processing {len(prompts)} chunk(s)...")

    def on_llm_end(self, response, **kwargs):
        print(f"✔️ Chunk processed!")

    def on_llm_error(self, error, **kwargs):
        print(f"❌ Error encountered: {error}")


parser = argparse.ArgumentParser(
    prog='summarizer',
    description='summarize a text document with ollama according to instructions')

parser.add_argument('filename', type=str, help='text document to be summarized.')
parser.add_argument('-i', '--initial-instructions', type=str,
                     help="instructions to ollama on how the document should initially be summarized (during the init/map step).")
parser.add_argument('-I', '--initial-instructions-file', type=str,
                    help="file containing instructions on how the document should initially be summarized (during the init/map step).")
parser.add_argument('-s', '--merge-instructions', type=str,
                    help="instructions on how the enhance or integration step should combine documents (during the refine/reduce step).")
parser.add_argument('-S', '--merge-instructions-file', type=str,
                    help="file containing instructions on how the enhance or integration step should combine documents (during the refine/reduce step).")
parser.add_argument('-m', '--model', type=str, help='model to use by ollama.')
parser.add_argument('-S', '--chunk-size', type=int,
                     help='size of chunks to break text into for summary.', default=1900)
parser.add_argument('-o', '--overlap', type=int,
                     help='size of overlap between chunks, to provide shared context.',
                     default=256)
parser.add_argument('-t', '--summary-type',
                     choices=['map_reduce', 'refine'],
                     help='what approach to use when summarizing: map_reduce (parallel) or refine (sequential).',
                     default='map_reduce')
parser.add_argument('-u', '--server', type=str,
                     help='URL of the ollama server.')
parser.add_argument('-v', '--verbose', action='store_true', help='provide verbose output.')


def read_file_contents(filename):
    content = None
    with open(filename) as f:
        content = f.read()
    return content


def main():

  args = parser.parse_args()

  if not os.path.isfile(args.filename):
      print(f"error: the file '{args.filename}' does not exist.")
      sys.exit(1)

  ollama_server = args.server
    
  if ollama_server is None:
    if os.getenv('OLLAMA_HOST') is None:
      print(f"error: server must be specified.")
      sys.exit(2)
    ollama_server = os.getenv('OLLAMA_HOST')

  ollama_model = args.model

  if ollama_model is None:
    if os.getenv('OLLAMA_MODEL') is None:
      ollama_client = ollama.Client(host=ollama_server)
      models = ollama_client.list()
      model_names = [model['name'] for model in models['models']]
      model_str = ", ".join(model_names)
      print(f"error: pick a model from one of the following options: {model_str}")
      sys.exit(2)
    ollama_model = os.getenv('OLLAMA_MODEL')

  init_step = None
  if args.initial_instructions is not None:
    init_step = args.initial_instructions
  elif args.initial_instructions_file is not None:
    init_step = read_file_contents(args.initial_instructions_file)
  else:
    print("error: no instructions provided, use -i or -I")
    sys.exit(2)

  merge_step = None
  if args.merge_instructions is not None:
    merge_step = args.merge_instructions
  elif args.merge_instructions_file is not None:
    merge_step = read_file_contents(args.merge_instructions_file)
  else:
    merge_step = init_step
    
  loader = TextLoader(args.filename)
  docs = loader.load()
  
  text_splitter = RecursiveCharacterTextSplitter(
      chunk_size=args.chunk_size,
      chunk_overlap=args.overlap)
  
  split_docs = text_splitter.split_documents(docs)

  if args.verbose:
    print(f"document split into {len(split_docs)} documents for summarization")
  
  llm = Ollama(model=ollama_model, base_url=ollama_server, num_ctx=2048)

  summarization_chain = None

  if args.summary_type == 'map_reduce':
    map_prompt = PromptTemplate.from_template(f"""
      Summarize text according to these instructions: {init_step}
      
      The text to be summarized is:
      
      {{text}}
    """)
    
    reduce_prompt = PromptTemplate.from_template(f"""
      Combine the following summaries according to the instructions: {merge_step}
      
      The summaries to be combined are:
      {{text}}
    """)
    
    summarization_chain = load_summarize_chain(
      llm,
      chain_type=args.summary_type,
      map_prompt=map_prompt,
      combine_prompt=reduce_prompt)
    
  elif args.summary_type == 'refine':
    question_prompt = PromptTemplate.from_template(f"""
      Summarize the following text according to these instructions: {init_step}
      
      The text to be summarized is:
      
      {{text}}
    """)

    refine_prompt = PromptTemplate.from_template(f"""
      We have a partial summary of a document. We need to update that summary with subsequent information.

      The current summary is as follows:

      {{existing_answer}}

      The new information to be integrated is as follows:

      {{text}}

      Integrate this new information into the existing summary according to the following instructions: {merge_step}
    """)

    summarization_chain = load_summarize_chain(
      llm,
      chain_type=args.summary_type,
      question_prompt=question_prompt,
      refine_prompt=refine_prompt)

  if args.verbose:
    print(f"summarizing the contents of file {args.filename} with the model {ollama_model}, with the instructions: {args.instructions}...")

  applied_callbacks = [PrintProgressCallback()] if args.verbose else []
  summary = summarization_chain.invoke(split_docs, callbacks=applied_callbacks)

  if args.verbose:
    print("summary complete!\n\n")
  
  print(summary['output_text'])

if __name__ == '__main__':
    main()
