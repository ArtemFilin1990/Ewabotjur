#!/usr/bin/env node
/**
 * DaData MCP Server
 * 
 * Provides Model Context Protocol (MCP) integration for DaData API.
 * DaData is a Russian data enrichment service for company verification,
 * address standardization, and entity data lookup.
 * 
 * Required Environment Variables:
 * - DADATA_API_KEY: DaData API key
 * - DADATA_SECRET_KEY: DaData secret key
 */

import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
  Tool,
} from '@modelcontextprotocol/sdk/types.js';
import axios, { AxiosInstance } from 'axios';
import * as dotenv from 'dotenv';

// Load environment variables
dotenv.config();

const DADATA_API_KEY = process.env.DADATA_API_KEY;
const DADATA_SECRET_KEY = process.env.DADATA_SECRET_KEY;
const DADATA_BASE_URL = 'https://suggestions.dadata.ru/suggestions/api/4_1/rs';
const DADATA_CLEAN_URL = 'https://cleaner.dadata.ru/api/v1/clean';

if (!DADATA_API_KEY || !DADATA_SECRET_KEY) {
  console.error('Error: DADATA_API_KEY and DADATA_SECRET_KEY environment variables are required');
  process.exit(1);
}

interface DaDataCompany {
  value: string;
  unrestricted_value: string;
  data: {
    inn?: string;
    ogrn?: string;
    kpp?: string;
    name?: {
      full_with_opf?: string;
      short_with_opf?: string;
    };
    address?: {
      value?: string;
      unrestricted_value?: string;
    };
    state?: {
      status?: string;
      liquidation_date?: string;
    };
    management?: {
      name?: string;
      post?: string;
    };
  };
}

interface DaDataAddress {
  value: string;
  unrestricted_value: string;
  data: {
    postal_code?: string;
    country?: string;
    region?: string;
    city?: string;
    street?: string;
    house?: string;
    geo_lat?: string;
    geo_lon?: string;
  };
}

class DaDataMCPServer {
  private server: Server;
  private axiosInstance: AxiosInstance;

  constructor() {
    this.server = new Server(
      {
        name: 'dadata-mcp-server',
        version: '1.0.0',
      },
      {
        capabilities: {
          tools: {},
        },
      }
    );

    this.axiosInstance = axios.create({
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'Authorization': `Token ${DADATA_API_KEY}`,
        'X-Secret': DADATA_SECRET_KEY,
      },
    });

    this.setupHandlers();
  }

  private setupHandlers() {
    // List available tools
    this.server.setRequestHandler(ListToolsRequestSchema, async () => {
      return {
        tools: this.getTools(),
      };
    });

    // Handle tool calls
    this.server.setRequestHandler(CallToolRequestSchema, async (request) => {
      const { name, arguments: args } = request.params;

      try {
        switch (name) {
          case 'dadata_suggest_company':
            return await this.suggestCompany(args as { query: string; count?: number });
          
          case 'dadata_find_by_id':
            return await this.findById(args as { query: string; type?: string });
          
          case 'dadata_suggest_address':
            return await this.suggestAddress(args as { query: string; count?: number });
          
          case 'dadata_clean_address':
            return await this.cleanAddress(args as { address: string });
          
          default:
            throw new Error(`Unknown tool: ${name}`);
        }
      } catch (error) {
        const errorMessage = error instanceof Error ? error.message : String(error);
        return {
          content: [
            {
              type: 'text',
              text: `Error: ${errorMessage}`,
            },
          ],
        };
      }
    });
  }

  private getTools(): Tool[] {
    return [
      {
        name: 'dadata_suggest_company',
        description: 'Search for Russian companies by name, INN, or OGRN. Returns company details including legal name, INN, OGRN, address, and legal status.',
        inputSchema: {
          type: 'object',
          properties: {
            query: {
              type: 'string',
              description: 'Company name, INN, or OGRN to search for',
            },
            count: {
              type: 'number',
              description: 'Number of suggestions to return (default: 10, max: 20)',
              default: 10,
            },
          },
          required: ['query'],
        },
      },
      {
        name: 'dadata_find_by_id',
        description: 'Find company or individual entrepreneur by exact INN or OGRN. Returns complete entity data.',
        inputSchema: {
          type: 'object',
          properties: {
            query: {
              type: 'string',
              description: 'INN or OGRN to find',
            },
            type: {
              type: 'string',
              description: 'Entity type: "party" for company/individual, "bank" for bank (default: party)',
              enum: ['party', 'bank'],
              default: 'party',
            },
          },
          required: ['query'],
        },
      },
      {
        name: 'dadata_suggest_address',
        description: 'Suggest and standardize Russian addresses. Returns structured address data with postal code, region, city, street, and coordinates.',
        inputSchema: {
          type: 'object',
          properties: {
            query: {
              type: 'string',
              description: 'Address to search and standardize',
            },
            count: {
              type: 'number',
              description: 'Number of suggestions to return (default: 10, max: 20)',
              default: 10,
            },
          },
          required: ['query'],
        },
      },
      {
        name: 'dadata_clean_address',
        description: 'Clean and standardize a single address. Parses free-form address into structured components.',
        inputSchema: {
          type: 'object',
          properties: {
            address: {
              type: 'string',
              description: 'Address to clean and standardize',
            },
          },
          required: ['address'],
        },
      },
    ];
  }

  private async suggestCompany(args: { query: string; count?: number }) {
    const { query, count = 10 } = args;
    
    const response = await this.axiosInstance.post<{ suggestions: DaDataCompany[] }>(
      `${DADATA_BASE_URL}/suggest/party`,
      {
        query,
        count: Math.min(count, 20),
      }
    );

    const suggestions = response.data.suggestions.map(s => ({
      name: s.data.name?.short_with_opf || s.value,
      full_name: s.data.name?.full_with_opf || s.unrestricted_value,
      inn: s.data.inn,
      ogrn: s.data.ogrn,
      kpp: s.data.kpp,
      address: s.data.address?.unrestricted_value,
      status: s.data.state?.status,
      liquidation_date: s.data.state?.liquidation_date,
      management: s.data.management ? {
        name: s.data.management.name,
        post: s.data.management.post,
      } : undefined,
    }));

    return {
      content: [
        {
          type: 'text',
          text: JSON.stringify({ query, count: suggestions.length, suggestions }, null, 2),
        },
      ],
    };
  }

  private async findById(args: { query: string; type?: string }) {
    const { query, type = 'party' } = args;
    
    const endpoint = type === 'bank' ? 'findById/bank' : 'findById/party';
    
    const response = await this.axiosInstance.post<{ suggestions: DaDataCompany[] }>(
      `${DADATA_BASE_URL}/${endpoint}`,
      {
        query,
      }
    );

    if (response.data.suggestions.length === 0) {
      return {
        content: [
          {
            type: 'text',
            text: JSON.stringify({ error: 'Entity not found', query }, null, 2),
          },
        ],
      };
    }

    const entity = response.data.suggestions[0];
    const result = {
      name: entity.data.name?.short_with_opf || entity.value,
      full_name: entity.data.name?.full_with_opf || entity.unrestricted_value,
      inn: entity.data.inn,
      ogrn: entity.data.ogrn,
      kpp: entity.data.kpp,
      address: entity.data.address?.unrestricted_value,
      status: entity.data.state?.status,
      liquidation_date: entity.data.state?.liquidation_date,
      management: entity.data.management ? {
        name: entity.data.management.name,
        post: entity.data.management.post,
      } : undefined,
    };

    return {
      content: [
        {
          type: 'text',
          text: JSON.stringify({ query, result }, null, 2),
        },
      ],
    };
  }

  private async suggestAddress(args: { query: string; count?: number }) {
    const { query, count = 10 } = args;
    
    const response = await this.axiosInstance.post<{ suggestions: DaDataAddress[] }>(
      `${DADATA_BASE_URL}/suggest/address`,
      {
        query,
        count: Math.min(count, 20),
      }
    );

    const suggestions = response.data.suggestions.map(s => ({
      value: s.value,
      unrestricted_value: s.unrestricted_value,
      postal_code: s.data.postal_code,
      country: s.data.country,
      region: s.data.region,
      city: s.data.city,
      street: s.data.street,
      house: s.data.house,
      coordinates: s.data.geo_lat && s.data.geo_lon ? {
        lat: s.data.geo_lat,
        lon: s.data.geo_lon,
      } : undefined,
    }));

    return {
      content: [
        {
          type: 'text',
          text: JSON.stringify({ query, count: suggestions.length, suggestions }, null, 2),
        },
      ],
    };
  }

  private async cleanAddress(args: { address: string }) {
    const { address } = args;
    
    const response = await this.axiosInstance.post<DaDataAddress[]>(
      `${DADATA_CLEAN_URL}/address`,
      [address]
    );

    if (response.data.length === 0) {
      return {
        content: [
          {
            type: 'text',
            text: JSON.stringify({ error: 'Unable to clean address', address }, null, 2),
          },
        ],
      };
    }

    const cleaned = response.data[0];
    const result = {
      original: address,
      value: cleaned.value,
      unrestricted_value: cleaned.unrestricted_value,
      postal_code: cleaned.data.postal_code,
      country: cleaned.data.country,
      region: cleaned.data.region,
      city: cleaned.data.city,
      street: cleaned.data.street,
      house: cleaned.data.house,
      coordinates: cleaned.data.geo_lat && cleaned.data.geo_lon ? {
        lat: cleaned.data.geo_lat,
        lon: cleaned.data.geo_lon,
      } : undefined,
    };

    return {
      content: [
        {
          type: 'text',
          text: JSON.stringify(result, null, 2),
        },
      ],
    };
  }

  async run() {
    const transport = new StdioServerTransport();
    await this.server.connect(transport);
    console.error('DaData MCP Server running on stdio');
  }
}

// Start the server
const server = new DaDataMCPServer();
server.run().catch((error) => {
  console.error('Fatal error:', error);
  process.exit(1);
});
