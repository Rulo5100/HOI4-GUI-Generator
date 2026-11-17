"""guigen's own shader for shader-mode line charts (EXPERIMENTAL: written against the structure of the
vanilla progress shaders, not tested in game; sprite mode is the default and needs no shader).

A progressbartype with `effectFile = "gfx/FX/guigen_line.lua"` and no textures runs the Color effect:

    color    = { width/1000  height/1000  line_width/10  area_alpha }   cell geometry, area fill alpha (0..1)
    colortwo = { r g b a }                                              line colour
    steps    = 1000000
    frame    = start_px * 1000 + end_px      heights in pixels from the bottom of the cell (0..999)

The engine loads gfx/FX/guigen_line.shader for the .lua name. `write_shaders(fs)` writes it.
"""

LINE_EFFECT = "gfx/FX/guigen_line.lua"
LINE_SHADER_PATH = "gfx/FX/guigen_line.shader"

LINE_SHADER = """Includes = {
}

PixelShader =
{
	Samplers =
	{
		TextureOne =
		{
			Index = 0
			MagFilter = "Point"
			MinFilter = "Point"
			MipFilter = "None"
			AddressU = "Wrap"
			AddressV = "Wrap"
		}
		TextureTwo =
		{
			Index = 1
			MagFilter = "Point"
			MinFilter = "Point"
			MipFilter = "None"
			AddressU = "Wrap"
			AddressV = "Wrap"
		}
	}
}

VertexStruct VS_INPUT
{
    float4 vPosition  : POSITION;
    float2 vTexCoord  : TEXCOORD0;
};

VertexStruct VS_OUTPUT
{
    float4  vPosition : PDX_POSITION;
    float2  vTexCoord0 : TEXCOORD0;
};

ConstantBuffer( 0, 0 )
{
	float4x4 WorldViewProjectionMatrix;
	float4 vFirstColor;
	float4 vSecondColor;
	float CurrentState;
};

VertexShader =
{
	MainCode VertexShader
	[[
		VS_OUTPUT main(const VS_INPUT v )
		{
			VS_OUTPUT Out;
			Out.vPosition  = mul( WorldViewProjectionMatrix, v.vPosition );
			Out.vTexCoord0  = v.vTexCoord;
			return Out;
		}
	]]
}

PixelShader =
{
	MainCode PixelColor
	[[
		float4 main( VS_OUTPUT v ) : PDX_COLOR
		{
			// guigen line segment: geometry in vFirstColor, colour in vSecondColor, ends in CurrentState
			float fWidth = vFirstColor.r * 1000.f;
			float fHeight = vFirstColor.g * 1000.f;
			float fLine = max( vFirstColor.b * 10.f, 0.5f );
			float fArea = vFirstColor.a;
			float fValue = floor( CurrentState * 1000000.f + 0.5f );
			float fStart = floor( fValue / 1000.f );
			float fEnd = fValue - fStart * 1000.f;
			float2 vP = float2( v.vTexCoord0.x * fWidth, ( 1.f - v.vTexCoord0.y ) * fHeight );
			float fSlope = ( fEnd - fStart ) / fWidth;
			float2 vA = float2( -1.f, fStart - fSlope );
			float2 vB = float2( fWidth + 1.f, fEnd + fSlope );
			float2 vAB = vB - vA;
			float fT = saturate( dot( vP - vA, vAB ) / dot( vAB, vAB ) );
			float fDist = length( vP - vA - vAB * fT );
			float fAlpha = saturate( fLine * 0.5f + 0.5f - fDist );
			float fLineY = lerp( fStart, fEnd, saturate( vP.x / fWidth ) );
			float fUnder = step( vP.y, fLineY ) * fArea;
			float4 vColor = vSecondColor;
			vColor.a = max( vSecondColor.a * fAlpha, vSecondColor.a * fUnder );
			return vColor;
		}
	]]

	MainCode PixelTexture
	[[
		float4 main( VS_OUTPUT v ) : PDX_COLOR
		{
			return float4( 1, 1, 1, 0 );
		}
	]]
}

BlendState BlendState
{
	BlendEnable = yes
	SourceBlend = "SRC_ALPHA"
	DestBlend = "INV_SRC_ALPHA"
}

Effect Color
{
	VertexShader = "VertexShader"
	PixelShader = "PixelColor"
}

Effect Texture
{
	VertexShader = "VertexShader"
	PixelShader = "PixelTexture"
}
"""


def line_frame(start_px, end_px):
    """Frame value for the line shader (heights in pixels from the bottom)."""
    return int(start_px) * 1000 + int(end_px)
