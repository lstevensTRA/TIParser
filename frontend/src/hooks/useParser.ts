import { useMutation } from '@tanstack/react-query';
import { parserAPI } from '../services/api';
import { ParserResponse } from '../types/parser.types';

export const useParser = () => {
  // WI Parser mutation
  const wiParserMutation = useMutation<ParserResponse, Error, File>({
    mutationFn: parserAPI.parseWI,
    retry: false, // Don't retry on failure
  });

  // AT Parser mutation
  const atParserMutation = useMutation<ParserResponse, Error, File>({
    mutationFn: parserAPI.parseAT,
    retry: false, // Don't retry on failure
  });

  // ROA Parser mutation
  const roaParserMutation = useMutation<ParserResponse, Error, File>({
    mutationFn: parserAPI.parseROA,
    retry: false, // Don't retry on failure
  });

  // TRT Parser mutation
  const trtParserMutation = useMutation<ParserResponse, Error, File>({
    mutationFn: parserAPI.parseTRT,
    retry: false, // Don't retry on failure
  });

  return {
    // WI Parser
    parseWI: wiParserMutation.mutate,
    parseWIAsync: wiParserMutation.mutateAsync,
    isParsingWI: wiParserMutation.isPending,
    wiParserError: wiParserMutation.error,
    wiParserData: wiParserMutation.data,

    // AT Parser
    parseAT: atParserMutation.mutate,
    parseATAsync: atParserMutation.mutateAsync,
    isParsingAT: atParserMutation.isPending,
    atParserError: atParserMutation.error,
    atParserData: atParserMutation.data,

    // ROA Parser
    parseROA: roaParserMutation.mutate,
    parseROAAsync: roaParserMutation.mutateAsync,
    isParsingROA: roaParserMutation.isPending,
    roaParserError: roaParserMutation.error,
    roaParserData: roaParserMutation.data,

    // TRT Parser
    parseTRT: trtParserMutation.mutate,
    parseTRTAsync: trtParserMutation.mutateAsync,
    isParsingTRT: trtParserMutation.isPending,
    trtParserError: trtParserMutation.error,
    trtParserData: trtParserMutation.data,

    // General parser state
    isParsing: wiParserMutation.isPending || atParserMutation.isPending || roaParserMutation.isPending || trtParserMutation.isPending,
  };
}; 