import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import { FireMap, googleMapsUrl, relativeUpdate } from '../FireMap';
describe('map',()=>{
 it('makes Google Maps coordinate URL',()=>expect(googleMapsUrl(-2.6701,111.7182)).toBe('https://www.google.com/maps/search/?api=1&query=-2.6701,111.7182'));
 it('formats relative source time',()=>expect(relativeUpdate('2026-10-19T00:00:00Z',new Date('2026-10-19T06:00:00Z'))).toBe('Updated 6 hours ago'));
 it('opens source detail sheet',()=>{render(<FireMap features={[{id:'x',geometry:{coordinates:[111.7182,-2.6701]},properties:{severity:'severe',source_url:'https://firms.modaps.eosdis.nasa.gov/',sensor:'VIIRS',satellite:'N',confidence:'nominal',island:'Kalimantan'}}]}/>);fireEvent.click(screen.getByRole('button',{name:/Severe fire/}));expect(screen.getByRole('complementary')).toHaveTextContent('NASA FIRMS');expect(screen.getByRole('link',{name:'Open in Google Maps'})).toHaveAttribute('href','https://www.google.com/maps/search/?api=1&query=-2.6701,111.7182');});
});
