#
# Ingest the files from the repository into Preservica
#
import click as CL
import dotenv as DOT
import pyPreservica as PRES
import r2plib


@CL.command()
@CL.argument('input', type=CL.File('r'))
def main(input):

    folder = r2plib.read_config(input.name)

    print(folder.max_submissions)
    
    DOT.load_dotenv()




if __name__ == "__main__":
    main()


