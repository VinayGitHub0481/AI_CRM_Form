
import {Bot} from 'lucide-react';

function Navbar() {

    return(
        <nav className='bg-blue-700 text-white px-6 py-4 shadow-md'>
            <div className='flex items-center gap-3'>
                <Bot size={28}  color="white" />
                <h1 className='text-2xl font-bold'>
                    AI Assistant 
                </h1>
            </div>
        </nav>

    );
}

export default Navbar;




















